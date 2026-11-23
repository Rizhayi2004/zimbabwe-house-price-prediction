
import json
import time
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from pathlib import Path
from PIL import Image, UnidentifiedImageError
from torch.utils.data import TensorDataset, DataLoader
from torchvision.models import resnet18, ResNet18_Weights
from transformers import AutoTokenizer, AutoModel

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "cleaned_house_listings.csv"
)

IMAGE_DIR = PROJECT_ROOT / "images" / "original"
RESULTS_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"

FEATURE_CACHE = RESULTS_DIR / "multimodal_features.npz"

DEVICE = torch.device("cpu")

TEXT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

BATCH_SIZE = 32
IMAGE_BATCH_SIZE = 16
MAX_TEXT_LENGTH = 128
EPOCHS = 120
PATIENCE = 15
LEARNING_RATE = 0.0005
RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "bedrooms",
    "bathrooms",
    "land_size",
    "floor_size",
    "garages"
]

CATEGORICAL_FEATURES = [
    "city",
    "suburb",
    "property_type"
]

STRUCTURED_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# ============================================================
# NEURAL NETWORK
# ============================================================

class MultimodalRegressor(nn.Module):

    def __init__(self, input_dimension):

        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_dimension, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(0.30),

            nn.Linear(512, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.20),

            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.10),

            nn.Linear(128, 1)
        )

    def forward(self, x):
        return self.network(x).squeeze(1)


# ============================================================
# IMAGE FEATURE EXTRACTION
# ============================================================

def find_listing_image(listing_id):

    candidates = []

    for path in IMAGE_DIR.iterdir():

        if not path.is_file():
            continue

        if path.stem.startswith(str(listing_id) + "_"):
            candidates.append(path)

        elif path.stem == str(listing_id):
            candidates.append(path)

    if not candidates:
        return None

    # Prefer the first numbered image when available.
    candidates.sort(
        key=lambda path: (
            0 if path.stem.endswith("_1") else 1,
            path.name
        )
    )

    return candidates[0]


def extract_image_features(listing_ids):

    print("\nLoading pretrained ResNet18...")

    weights = ResNet18_Weights.DEFAULT

    model = resnet18(weights=weights)
    model.fc = nn.Identity()
    model.eval()
    model.to(DEVICE)

    transform = weights.transforms()

    features = np.zeros((len(listing_ids), 512), dtype=np.float32)
    image_present = np.zeros(len(listing_ids), dtype=np.float32)

    batch_images = []
    batch_indices = []

    def process_batch():

        if not batch_images:
            return

        tensor = torch.stack(batch_images).to(DEVICE)

        with torch.no_grad():
            output = model(tensor)

        output = output.cpu().numpy()

        for index, vector in zip(batch_indices, output):
            features[index] = vector

        batch_images.clear()
        batch_indices.clear()

    print("\nExtracting image features...")

    for index, listing_id in enumerate(listing_ids):

        path = find_listing_image(listing_id)

        if path is None:
            continue

        try:
            with Image.open(path) as image:
                image = image.convert("RGB")
                tensor = transform(image)

            batch_images.append(tensor)
            batch_indices.append(index)
            image_present[index] = 1.0

        except (OSError, UnidentifiedImageError) as error:
            print("Image could not be read:", path.name, error)

        if len(batch_images) >= IMAGE_BATCH_SIZE:
            process_batch()

        if (index + 1) % 200 == 0:
            print(
                f"Image records checked: {index + 1}/{len(listing_ids)}"
            )

    process_batch()

    print("Image extraction completed.")
    print("Listings with images:", int(image_present.sum()))
    print("Listings without images:", int(len(listing_ids) - image_present.sum()))

    return features, image_present


# ============================================================
# TEXT FEATURE EXTRACTION
# ============================================================

def extract_text_features(df):

    print("\nLoading pretrained MiniLM...")

    tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_NAME)
    model = AutoModel.from_pretrained(TEXT_MODEL_NAME)

    model.eval()
    model.to(DEVICE)

    texts = []

    for _, row in df.iterrows():

        description = (
            str(row["description"])
            if pd.notna(row["description"])
            else ""
        )

        property_features = (
            str(row["features"])
            if pd.notna(row["features"])
            else ""
        )

        combined = (
            "Property description: "
            + description
            + " Property features: "
            + property_features
        )

        texts.append(combined)

    embeddings = []

    print("\nExtracting text embeddings...")

    for start in range(0, len(texts), BATCH_SIZE):

        batch = texts[start:start + BATCH_SIZE]

        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=MAX_TEXT_LENGTH,
            return_tensors="pt"
        )

        encoded = {
            key: value.to(DEVICE)
            for key, value in encoded.items()
        }

        with torch.no_grad():
            output = model(**encoded)

            mask = encoded["attention_mask"].unsqueeze(-1)

            pooled = (
                (output.last_hidden_state * mask).sum(dim=1)
                / mask.sum(dim=1).clamp(min=1)
            )

        embeddings.append(pooled.cpu().numpy())

        if (start + len(batch)) % 200 == 0:
            print(
                f"Text records processed: {start + len(batch)}/{len(texts)}"
            )

    embeddings = np.vstack(embeddings).astype(np.float32)

    print("Text extraction completed.")
    print("Text feature shape:", embeddings.shape)

    return embeddings


# ============================================================
# FEATURE CACHE
# ============================================================

def get_multimodal_features(df):

    listing_ids = df["listing_id"].astype(str).to_numpy()

    if FEATURE_CACHE.exists():

        print("\nChecking existing feature cache...")

        cached = np.load(FEATURE_CACHE)

        cached_ids = cached["listing_ids"].astype(str)

        if np.array_equal(cached_ids, listing_ids):

            print("Using verified cached features.")

            return (
                cached["image_features"],
                cached["image_present"],
                cached["text_features"]
            )

        print("Cache does not match current dataset. Rebuilding.")

    image_features, image_present = extract_image_features(
        listing_ids
    )

    text_features = extract_text_features(df)

    np.savez_compressed(
        FEATURE_CACHE,
        listing_ids=listing_ids,
        image_features=image_features,
        image_present=image_present,
        text_features=text_features
    )

    print("\nSaved feature cache:", FEATURE_CACHE)

    return image_features, image_present, text_features


# ============================================================
# STRUCTURED DATA PREPROCESSING
# ============================================================

def create_preprocessor():

    numeric_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(
                strategy="median",
                add_indicator=True
            )
        ),
        (
            "scaler",
            StandardScaler()
        )
    ])

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(
                strategy="constant",
                fill_value="Missing"
            )
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            )
        )
    ])

    return ColumnTransformer([
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES)
    ])


# ============================================================
# EVALUATION
# ============================================================

def evaluate_model(actual, predictions):

    return {
        "MAE_USD": float(
            mean_absolute_error(actual, predictions)
        ),
        "RMSE_USD": float(
            np.sqrt(mean_squared_error(actual, predictions))
        ),
        "R2": float(
            r2_score(actual, predictions)
        )
    }


# ============================================================
# TRAINING
# ============================================================

def train_model():

    start_time = time.time()

    if not DATA_FILE.exists():
        raise FileNotFoundError(DATA_FILE)

    if not IMAGE_DIR.exists():
        raise FileNotFoundError(IMAGE_DIR)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading cleaned dataset...")

    df = pd.read_csv(DATA_FILE)

    required = (
        STRUCTURED_FEATURES
        + [
            "listing_id",
            "price",
            "currency",
            "description",
            "features"
        ]
    )

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["price"] = pd.to_numeric(
        df["price"],
        errors="coerce"
    )

    for column in NUMERIC_FEATURES:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=["listing_id", "price", "currency"]
    )

    df = df[df["price"] > 0].copy()

    currencies = (
        df["currency"].astype(str).str.upper().unique()
    )

    if len(currencies) != 1 or currencies[0] != "USD":
        raise ValueError(
            f"Expected USD-only data. Found: {currencies}"
        )

    df = df.reset_index(drop=True)

    print("\nDATASET")
    print("Records:", len(df))
    print("Currency:", currencies[0])

    # Extract fixed pretrained embeddings.
    image_features, image_present, text_features = (
        get_multimodal_features(df)
    )

    # Reproduce the same 80/20 test split as Extra Trees.
    indices = np.arange(len(df))

    train_indices, test_indices = train_test_split(
        indices,
        test_size=0.2,
        random_state=RANDOM_STATE
    )

    print("\nDATA SPLIT")
    print("Training records:", len(train_indices))
    print("Testing records:", len(test_indices))

    X = df[STRUCTURED_FEATURES]
    y = df["price"].to_numpy(dtype=np.float32)

    # Fit structured preprocessing on training data only.
    preprocessor = create_preprocessor()

    X_train_structured = preprocessor.fit_transform(
        X.iloc[train_indices]
    )

    X_test_structured = preprocessor.transform(
        X.iloc[test_indices]
    )

    X_train_structured = np.asarray(
        X_train_structured,
        dtype=np.float32
    )

    X_test_structured = np.asarray(
        X_test_structured,
        dtype=np.float32
    )

    # Fit embedding scalers on training data only.
    image_scaler = StandardScaler()
    text_scaler = StandardScaler()

    image_train = image_scaler.fit_transform(
        image_features[train_indices]
    )

    image_test = image_scaler.transform(
        image_features[test_indices]
    )

    text_train = text_scaler.fit_transform(
        text_features[train_indices]
    )

    text_test = text_scaler.transform(
        text_features[test_indices]
    )

    # Keep missing-image indicator as an additional feature.
    image_train = np.column_stack([
        image_train,
        image_present[train_indices]
    ])

    image_test = np.column_stack([
        image_test,
        image_present[test_indices]
    ])

    X_train = np.concatenate([
        X_train_structured,
        image_train,
        text_train
    ], axis=1).astype(np.float32)

    X_test = np.concatenate([
        X_test_structured,
        image_test,
        text_test
    ], axis=1).astype(np.float32)

    y_train = y[train_indices]
    y_test = y[test_indices]

    # Scale target for stable neural-network training.
    target_mean = float(y_train.mean())
    target_std = float(y_train.std())

    if target_std == 0:
        raise ValueError("Training target has zero variation.")

    y_train_scaled = (
        (y_train - target_mean) / target_std
    ).astype(np.float32)

    # Create internal validation split from training records only.
    fit_indices, validation_indices = train_test_split(
        np.arange(len(X_train)),
        test_size=0.15,
        random_state=RANDOM_STATE
    )

    X_fit = torch.tensor(X_train[fit_indices])
    y_fit = torch.tensor(y_train_scaled[fit_indices])

    X_validation = torch.tensor(X_train[validation_indices])
    y_validation = torch.tensor(y_train_scaled[validation_indices])

    X_test_tensor = torch.tensor(X_test)

    train_dataset = TensorDataset(X_fit, y_fit)

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        drop_last=False
    )

    model = MultimodalRegressor(
        input_dimension=X_train.shape[1]
    ).to(DEVICE)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=0.0001
    )

    loss_function = nn.HuberLoss()

    best_loss = float("inf")
    best_state = None
    patience_counter = 0

    print("\nMODEL")
    print("Input features:", X_train.shape[1])
    print("Architecture: 512 -> 256 -> 128 -> 1")
    print("Device:", DEVICE)
    print("\nTraining multimodal neural network...")

    for epoch in range(EPOCHS):

        model.train()
        training_losses = []

        for batch_X, batch_y in train_loader:

            optimizer.zero_grad()

            predictions = model(batch_X)

            loss = loss_function(predictions, batch_y)

            loss.backward()

            optimizer.step()

            training_losses.append(loss.item())

        model.eval()

        with torch.no_grad():
            validation_predictions = model(X_validation)

            validation_loss = loss_function(
                validation_predictions,
                y_validation
            ).item()

        if validation_loss < best_loss:

            best_loss = validation_loss

            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

            patience_counter = 0

        else:
            patience_counter += 1

        if (epoch + 1) % 10 == 0 or epoch == 0:

            print(
                f"Epoch {epoch + 1}/{EPOCHS} | "
                f"Training loss: {np.mean(training_losses):.5f} | "
                f"Validation loss: {validation_loss:.5f}"
            )

        if patience_counter >= PATIENCE:

            print(
                f"\nEarly stopping at epoch {epoch + 1}."
            )
            break

    if best_state is None:
        raise RuntimeError("Training did not produce a valid model.")

    model.load_state_dict(best_state)
    model.eval()

    with torch.no_grad():
        scaled_predictions = model(
            X_test_tensor
        ).cpu().numpy()

    predictions = (
        scaled_predictions * target_std + target_mean
    )

    predictions = np.maximum(predictions, 0)

    if not np.isfinite(predictions).all():
        raise ValueError("Non-finite predictions detected.")

    metrics = evaluate_model(y_test, predictions)

    print("\nMULTIMODAL MODEL RESULTS")
    print("MAE (USD):", round(metrics["MAE_USD"], 2))
    print("RMSE (USD):", round(metrics["RMSE_USD"], 2))
    print("R-squared:", round(metrics["R2"], 4))

    # Save neural network.
    model_path = MODEL_DIR / "multimodal_model.pt"

    torch.save({
        "model_state_dict": model.state_dict(),
        "input_dimension": X_train.shape[1],
        "target_mean": target_mean,
        "target_std": target_std,
        "architecture": "512-256-128-1",
        "text_model": TEXT_MODEL_NAME,
        "image_model": "ResNet18"
    }, model_path)

    # Save preprocessing objects.
    preprocessing_path = (
        MODEL_DIR / "multimodal_preprocessor.joblib"
    )

    joblib.dump({
        "structured_preprocessor": preprocessor,
        "image_scaler": image_scaler,
        "text_scaler": text_scaler,
        "features": STRUCTURED_FEATURES
    }, preprocessing_path)

    # Save metrics.
    results = {
        "multimodal": metrics,
        "dataset_records": int(len(df)),
        "training_records": int(len(train_indices)),
        "testing_records": int(len(test_indices)),
        "image_records": int(image_present.sum()),
        "missing_image_records": int(
            len(image_present) - image_present.sum()
        ),
        "image_embedding_dimension": 512,
        "text_embedding_dimension": 384,
        "random_state": RANDOM_STATE,
        "target": "raw USD asking price",
        "best_validation_loss": float(best_loss)
    }

    metrics_path = (
        RESULTS_DIR / "multimodal_model_results.json"
    )

    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    # Save predictions with original row indices.
    prediction_data = pd.DataFrame({
        "actual_price_USD": y_test,
        "multimodal_prediction": predictions
    }, index=test_indices)

    predictions_path = (
        RESULTS_DIR / "multimodal_predictions.csv"
    )

    prediction_data.to_csv(
        predictions_path,
        index_label="row_index"
    )

    print("\nSAVED OUTPUTS")
    print("Model:", model_path)
    print("Preprocessing:", preprocessing_path)
    print("Metrics:", metrics_path)
    print("Predictions:", predictions_path)
    print("Feature cache:", FEATURE_CACHE)

    print("\nElapsed minutes:", round(
        (time.time() - start_time) / 60, 2
    ))

    print("\nMULTIMODAL TRAINING COMPLETED")


if __name__ == "__main__":
    train_model()
