
# Zimbabwe House Price Prediction

## 1. Project Overview

This project investigates the factors associated with advertised house prices in Zimbabwe and evaluates machine learning models for predicting property asking prices.

The research question is:

**Which features explain the asking prices of houses for sale in Zimbabwe, and how accurately can a model predict them?**

The project uses property listings collected from [Property.co.zw](https://www.property.co.zw/houses-for-sale). It combines structured property characteristics, listing descriptions and property images to investigate both conventional machine learning and multimodal deep learning approaches.

## 2. Objectives

- Collect a dataset of 2,400 house listings in Zimbabwe.
- Clean and prepare property listing data for analysis.
- Explore relationships between property characteristics and asking prices.
- Train and compare linear regression, Random Forest, Extra Trees and a multimodal neural network.
- Investigate the contribution of property characteristics to prediction performance.
- Evaluate models using MAE, RMSE and R-squared.
- Identify limitations and opportunities for improving property price prediction.

## 3. Dataset

The dataset contains 2,400 property listings and 21 columns.

The information includes:

- Asking price and currency.
- City, suburb and region.
- Bedrooms, bathrooms and garages.
- Land size and floor size.
- Property type.
- Property descriptions and advertised features.
- Property image references and downloaded image filenames.
- Listing and collection dates.

The cleaned dataset is stored at:

`data/processed/cleaned_house_listings.csv`

The data dictionary is available at:

`data/processed/data_dictionary.csv`

All asking prices in the modelling dataset are denominated in USD.

### Data collection

Listings were collected from Property.co.zw using Python scraping scripts.

The collection process included:
- Extracting listing details.
- Recording property descriptions and features.
- Collecting available image URLs.
- Downloading property images.
- Recording collection dates and listing identifiers.

The image collection process was audited. Four listings had no successfully available local images. These records were retained rather than discarded.

The dataset represents advertised asking prices, not confirmed property transaction prices.

## 4. Project Structure

zimbabwe-house-price-prediction/
│
├── data/
│   ├── raw/
│   │   └── house_listings.csv
│   └── processed/
│       ├── cleaned_house_listings.csv
│       ├── data_dictionary.csv
│       ├── cleaning_report.txt
│       ├── model_comparison.csv
│       ├── multimodal_features.npz
│       └── EDA summaries, model results and predictions
│
├── images/
│   └── original/
│       └── Downloaded property listing images
│
├── models/
│   ├── linear_raw.joblib
│   ├── linear_log.joblib
│   ├── random_forest.joblib
│   ├── extra_trees.joblib
│   ├── multimodal_model.pt
│   └── multimodal_preprocessor.joblib
│
├── notebooks/
│   └── Reserved for future Jupyter notebooks
│
├── research/
│   └── Website inspection, pagination investigation
│       and exploratory testing scripts
│
├── report/
│   ├── figures/
│   │   ├── EDA figures
│   │   ├── model_comparison.png
│   │   └── residual diagnostic figures
│   └── residual_diagnostics_summary.txt
│
├── src/
│   └── Data collection, cleaning, modelling,
│       prediction and analysis scripts
│
├── .gitattributes
├── .gitignore
├── requirements.txt
└── README.md


## 5. Data Preparation and Exploratory Analysis

Data preparation involved:
- Removing duplicate or invalid records where necessary.
- Converting numeric property attributes into appropriate numeric types.
- Handling missing and invalid measurements.
- Correcting identified data-entry anomalies where supported by the source listing.
- Checking currency consistency.
- Producing a cleaned dataset and cleaning report.

Exploratory data analysis examined:
- Asking-price distributions.
- Property prices by city and property type.
- Bedroom counts and asking prices.
- Land size and floor size relationships.
- Missing-value patterns.
- Correlations between numerical property characteristics.

The asking-price distribution is strongly right-skewed, with a small number of expensive properties.

## 6. Modelling Methodology

All models use an 80/20 training and testing split with random state 42:

- Training records: 1,920.
- Testing records: 480.

The models predict raw USD asking prices.

### 6.1 Linear Regression

Linear regression provides a baseline for comparing more complex models.

Two versions were evaluated:
- Linear regression trained on raw asking prices.
- Linear regression trained on log-transformed asking prices.

### 6.2 Random Forest

Random Forest uses an ensemble of decision trees to model nonlinear relationships between property attributes and asking prices.

### 6.3 Extra Trees

Extra Trees is an ensemble learning approach that introduces additional randomisation when constructing decision trees.

It was evaluated using 500 trees and a minimum leaf size of two.

### 6.4 Multimodal Neural Network

The multimodal model combines three information sources:

**Structured data**
- Bedrooms.
- Bathrooms.
- Garages.
- Land size.
- Floor size.
- City.
- Suburb.
- Property type.

**Image features**

A pretrained ResNet18 convolutional neural network extracts 512-dimensional image embeddings.

**Text features**

A pretrained MiniLM transformer generates 384-dimensional embeddings from property descriptions and advertised features.

The combined feature representation is passed into a multilayer perceptron neural network.

The model uses a validation split, Huber loss, AdamW optimisation and early stopping.

Listings without available images are retained using zero image embeddings and a missing-image indicator.

## 7. Model Evaluation

Models were evaluated on the same 480 test records using:

- **Mean Absolute Error (MAE):** Average absolute prediction error in USD.
- **Root Mean Squared Error (RMSE):** Penalises larger prediction errors more heavily.
- **R-squared (R²):** Measures the proportion of test-set price variation explained by the model relative to predicting the test mean.

### Model comparison

| Model | MAE (USD) | RMSE (USD) | R² |
|---|---:|---:|---:|
| Extra Trees | 106,640.89 | 206,230.97 | 0.6719 |
| Random Forest | 119,264.02 | 223,303.56 | 0.6153 |
| Linear Regression (Raw) | 122,949.15 | 296,450.10 | 0.3220 |
| Multimodal Neural Network | 126,551.10 | 243,095.67 | 0.5441 |
| Linear Regression (Log) | 127,195.52 | 535,457.06 | -1.2119 |

**Best-performing model: Extra Trees**

Extra Trees achieved the lowest MAE and RMSE and the highest R² among the evaluated models.

Its R² of 0.6719 indicates that it explains approximately 67.19% of the variation in asking prices in the held-out test set, relative to the test-set mean baseline.

The multimodal neural network performed better than the linear regression models on RMSE and R² in the reported comparison, but did not outperform Extra Trees.

This indicates that adding image and text embeddings did not improve predictive accuracy over the strongest structured-data model in this experiment.

## 8. Feature Importance

Permutation importance was used to investigate the contribution of structured predictors to model performance.

The Extra Trees results identified the following important predictors:

1. Suburb.
2. Land size.
3. Bathrooms.
4. City.
5. Floor size.
6. Bedrooms.
7. Garages.

These results suggest that location and property size are particularly informative when predicting advertised house prices.

Permutation importance measures predictive contribution in the evaluated model. It does not establish causal relationships.

## 9. Error Analysis and Residual Diagnostics

Prediction errors were examined to identify listings that were difficult to predict.

The model showed larger errors on some expensive and unusual properties, including luxury listings and properties with uncommon measurements.

Residual diagnostics were generated to investigate:
- Actual versus predicted prices.
- Residuals versus predicted prices.
- Residual distribution.
- Absolute prediction error distribution.

These diagnostics help assess model behaviour and identify potential systematic errors.

## 10. Limitations

The project has several limitations:

- The dataset is based on listings from one property website.
- Harare accounts for a substantial proportion of the collected sample.
- Asking prices may differ from actual transaction prices.
- Some property measurements and features are missing.
- Four listings had no available local images.
- Luxury properties and unusual listings can produce large prediction errors.
- The dataset is relatively small for training a multimodal deep learning model.
- A single train/test split does not establish performance across all possible samples or future market conditions.
- Model feature importance does not imply causation.

## 11. Technologies Used

- Python
- Pandas and NumPy
- Matplotlib
- Scikit-learn
- PyTorch
- Torchvision
- Hugging Face Transformers
- ResNet18
- MiniLM
- Joblib


## 12. Running the Project

### Requirements

- Python 3.11 or a compatible version.
- Dependencies listed in `requirements.txt`.
- Internet access for collecting listings and downloading pretrained model weights.
- Sufficient disk space for listing images, datasets and model files.

### Installation

Clone the repository:

```powershell
git clone https://github.com/Rizhayi2004/zimbabwe-house-price-prediction.git
cd zimbabwe-house-price-prediction
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Data collection (optional)

The project includes scripts for inspecting the website and collecting listings.

```powershell
python src\inspect_site.py
python src\test_parser.py
python src\scrape_listings.py
python src\collect_data.py
python src\check_collection.py
```

Additional collection and listing-ID correction scripts are also available in `src/`.

Collection scripts should only be run when new data is required. Respect the source website's terms of use and apply appropriate request delays.

### Reproducing the experiments

If the collected dataset is already available at `data/raw/house_listings.csv`, begin with data preparation:

```powershell
python src\clean_data.py
python src\explore_data.py
```

Train the models:

```powershell
python src\train_baseline.py
python src\train_random_forest.py
python src\train_extra_trees.py
python src\train_multimodal.py
```

Compare model performance:

```powershell
python src\compare_models.py
```

Run model analysis and diagnostics:

```powershell
python src\analyze_random_forest.py
python src\analyze_random_forest_errors.py
python src\analyze_extra_trees.py
python src\analyze_extra_trees_errors.py
python src\residual_diagnostics.py
```

The image downloader can be run separately when listing images need to be retrieved:

```powershell
python src\download_images.py
```

The multimodal model uses pretrained ResNet18 and MiniLM weights. These are downloaded or loaded from the local cache when required.

Some scripts depend on outputs generated by earlier stages. Run the relevant stages in sequence and ensure that the required input files are available.

## 13. Reproducibility

The main model experiments use a fixed random state of 42 for the train/test split.

Model results, prediction files, feature importance outputs and diagnostic figures are saved in the project directories.

The original raw dataset is retained separately from the cleaned dataset.

## 14. Research Conclusion

The results demonstrate that machine learning can capture useful relationships between property characteristics and advertised house prices in Zimbabwe.

Among the evaluated approaches, Extra Trees achieved the strongest predictive performance, with an MAE of approximately USD 106,641 and an R² of 0.6719.

Location, land size, bathrooms and floor size were among the most informative structured predictors.

Although the multimodal model incorporated image and text representations, it did not outperform Extra Trees. Further research could explore larger datasets, improved image processing, more representative geographical coverage and stronger multimodal architectures.
