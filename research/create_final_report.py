from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "report"
FIGURES = REPORT_DIR / "figures"
OUTPUT = REPORT_DIR / "final_report.docx"

doc = Document()
section = doc.sections[0]
section.page_width = Inches(8.27)
section.page_height = Inches(11.69)
section.top_margin = Inches(0.55)
section.bottom_margin = Inches(0.55)
section.left_margin = Inches(0.65)
section.right_margin = Inches(0.65)

styles = doc.styles
styles["Normal"].font.name = "Arial"
styles["Normal"].font.size = Pt(9)
styles["Normal"].paragraph_format.space_after = Pt(4)
styles["Normal"].paragraph_format.line_spacing = 1.0

for style_name, size in [("Title", 23), ("Heading 1", 15), ("Heading 2", 11)]:
    style = styles[style_name]
    style.font.name = "Arial"
    style.font.size = Pt(size)
    style.font.bold = True
    style.font.color.rgb = RGBColor(31, 78, 121)
    style.paragraph_format.space_before = Pt(5)
    style.paragraph_format.space_after = Pt(4)

def shade(cell, fill="D9EAF7"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)

def set_cell_text(cell, value, bold=False, size=8):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(str(value))
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(size)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def add_table(headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, heading in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], heading, True, 8)
        shade(table.rows[0].cells[i])
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, False, 8)
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table

def para(text="", bold_start=None, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.keep_together = True
    if bold_start and text.startswith(bold_start):
        r = p.add_run(bold_start)
        r.bold = True
        p.add_run(text[len(bold_start):])
    else:
        r = p.add_run(text)
        r.italic = italic
    return p

def heading(text, level=1):
    doc.add_heading(text, level=level)

def figure(filename, caption, width=5.8):
    path = FIGURES / filename
    if not path.exists():
        para(f"[Figure unavailable: {filename}]")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(path), width=Inches(width))
    cp = doc.add_paragraph(caption)
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(4)
    for run in cp.runs:
        run.italic = True
        run.font.size = Pt(8)

def page_title(text):
    p = doc.add_heading(text, level=1)
    p.paragraph_format.keep_with_next = True

# Header and footer
header = section.header.paragraphs[0]
header.text = "ZIMBABWE HOUSE PRICE PREDICTION | MINI RESEARCH PROJECT"
header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
for r in header.runs:
    r.font.size = Pt(7)
    r.font.color.rgb = RGBColor(100, 100, 100)

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = footer.add_run("House Price Prediction Research Report  •  ")
run.font.size = Pt(8)
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
footer._p.append(field)

# PAGE 1
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(30)
r = p.add_run("ZIMBABWE HOUSE PRICE\nPREDICTION")
r.bold = True
r.font.name = "Arial"
r.font.size = Pt(24)
r.font.color.rgb = RGBColor(31, 78, 121)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Explaining asking prices and evaluating predictive models")
r.italic = True
r.font.size = Pt(12)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(8)
p.add_run("Mini Research Project | 23 November 2026").bold = True

heading("Abstract")
para(
    "This study investigates which property characteristics help explain advertised house "
    "prices in Zimbabwe and evaluates how accurately machine-learning models can predict "
    "those asking prices. A dataset of 2,400 house listings was collected from Property.co.zw "
    "between 21 and 23 November 2026. Structured property information, descriptions and "
    "available listing photographs were prepared for analysis. Four modelling approaches "
    "were evaluated using the same fixed 80/20 train-test split. Extra Trees achieved the "
    "best test performance, with a mean absolute error (MAE) of US$106,640.89, root mean "
    "squared error (RMSE) of US$206,230.97 and R-squared of 0.6719. Location, land size, "
    "bathrooms and floor size were among the most informative predictors. A multimodal "
    "neural network combining structured, image and text features did not outperform "
    "Extra Trees. The results indicate useful predictive patterns, but substantial errors "
    "remain, particularly for expensive properties."
)

heading("1. Introduction")
para(
    "Property asking prices can vary with location, property size, accommodation and other "
    "features. Understanding these relationships can support market analysis and provide "
    "a basis for estimating advertised prices. However, asking prices are not necessarily "
    "the prices at which properties eventually sell."
)
para(
    "The research question is: Which features explain the asking prices of houses for sale "
    "in Zimbabwe, and how accurately can a model predict them?"
)
heading("Study objectives", 2)
for item in [
    "Collect and prepare at least 2,400 online house listings.",
    "Explore price patterns and relationships between prices and property characteristics.",
    "Compare a linear baseline, tree-based models and a multimodal neural network.",
    "Evaluate prediction errors and identify important limitations."
]:
    para("• " + item)

# PAGE 2
doc.add_page_break()
page_title("2. Data and exploratory analysis")
heading("2.1 Data collection")
para(
    "Listings were collected from Property.co.zw's houses-for-sale pages. The final raw "
    "dataset contains 2,400 records and 21 fields, including listing identifier, title, "
    "asking price, currency, city, suburb, bedrooms, bathrooms, garages, land size, floor "
    "size, property type, description, features, image URLs and collection date. The "
    "collection snapshot spans 21–23 November 2026. Requests were spaced using delays "
    "and retry handling; compliance with all website terms was not independently verified."
)
heading("2.2 Data cleaning")
para(
    "The cleaning process standardised text fields and currency labels, converted numeric "
    "measurements, removed duplicate listing identifiers and excluded records with invalid "
    "or missing/non-positive prices. No duplicate records or invalid prices were found, "
    "so all 2,400 records were retained. Two implausible bathroom values were changed to "
    "missing, and 16 land/floor-size values were reviewed and corrected or set to missing "
    "where they could not be reliably interpreted. Missing property measurements were "
    "preserved and handled during model preprocessing rather than deleting those listings."
)
para(
    "All retained asking prices were in US dollars. Missing values were most common for "
    "garages (1,888 records), land size (862), features (474), floor size (292) and "
    "bathrooms (273). Bedrooms had two missing values. A total of 2,396 listings had at "
    "least one downloaded photograph; four listings had no usable downloaded image."
)
heading("2.3 Descriptive findings")
add_table(
    ["Statistic", "Result"],
    [
        ["Number of listings", "2,400"],
        ["Mean asking price", "US$312,782"],
        ["Median asking price", "US$190,000"],
        ["Minimum / maximum", "US$110 / US$7,500,000"],
        ["Price standard deviation", "US$386,439"],
        ["Harare listings", "1,654 (approximately 68.9%)"],
    ],
    [2.7, 3.0]
)
para(
    "The price distribution is strongly right-skewed (skewness 5.223), with a small number "
    "of very expensive listings raising the mean above the median. Spearman correlations "
    "with asking price were strongest for land size (0.670), floor size (0.559), bathrooms "
    "(0.541), garages (0.431) and bedrooms (0.386). These are associations, not evidence "
    "that any feature causes a price change."
)
figure("correlation_heatmap.png",
       "Figure 1. Spearman correlations among numerical property variables.", 5.0)

# PAGE 3
doc.add_page_break()
page_title("3. Modelling methodology")
heading("3.1 Dataset split and predictors")
para(
    "The target variable was the raw US-dollar asking price. The dataset was divided into "
    "80% training data (1,920 listings) and 20% test data (480 listings), using "
    "random_state=42. The same split was used for the reported model comparison. Eight "
    "predictors were used: bedrooms, bathrooms, land size, floor size, garages, city, "
    "suburb and property type."
)
heading("3.2 Preprocessing and baseline")
para(
    "Numerical missing values were imputed using training-set medians, with missingness "
    "indicators added. Categorical missing values were assigned a 'Missing' category, and "
    "one-hot encoding represented categorical variables. The baseline was linear "
    "regression on raw prices. A second linear regression model was trained on log1p "
    "prices and its predictions transformed back to dollars."
)
heading("3.3 Tree-based models")
para(
    "Random Forest and Extra Trees regressors each used 500 trees, min_samples_leaf=2 "
    "and max_features=0.8, with random_state=42. These ensemble methods can represent "
    "non-linear relationships and interactions between property characteristics. "
    "Preprocessing was fitted on training data only."
)
heading("3.4 Multimodal neural network")
para(
    "The multimodal model combined three feature groups. Structured variables were "
    "preprocessed using median imputation, missing indicators, scaling and one-hot "
    "encoding. For images, a pretrained ResNet18 had its final classification layer "
    "removed and produced 512-dimensional embeddings; its weights were frozen and used "
    "as a feature extractor. For text, the pretrained all-MiniLM-L6-v2 transformer "
    "produced 384-dimensional mean-pooled embeddings from listing descriptions and "
    "features, truncated to 128 tokens. These pretrained feature extractors were not "
    "fine-tuned."
)
para(
    "The three feature groups were concatenated, with an image-present indicator. Missing "
    "images were represented by zero image embeddings and an absent-image flag. A fully "
    "connected network with hidden layers of 512, 256 and 128 units used ReLU activations, "
    "batch normalisation and dropout. It was trained with AdamW and Huber loss, using "
    "early stopping on an internal validation subset. The target was standardised during "
    "training and predictions were converted back to US dollars."
)
heading("3.5 Evaluation")
para(
    "Models were compared on the held-out test set using MAE, RMSE and R-squared. MAE "
    "measures the average absolute dollar error; RMSE penalises large errors more heavily; "
    "R-squared measures the proportion of test-target variance explained by the model. "
    "Permutation importance for Extra Trees was calculated on the test set using "
    "negative MAE, 10 repeats and random_state=42."
)

# PAGE 4
doc.add_page_break()
page_title("4. Results and interpretation")
heading("4.1 Test-set model comparison")
add_table(
    ["Model", "MAE (US$)", "RMSE (US$)", "R²"],
    [
        ["Linear Regression (raw)", "122,949.15", "296,450.10", "0.3220"],
        ["Linear Regression (log)", "127,195.52", "535,457.06", "-1.2119"],
        ["Random Forest", "119,264.02", "223,303.56", "0.6153"],
        ["Extra Trees", "106,640.89", "206,230.97", "0.6719"],
        ["Multimodal neural network", "126,551.10", "243,095.67", "0.5441"],
    ],
    [2.0, 1.45, 1.45, 0.65]
)
figure("model_comparison.png",
       "Figure 2. Comparison of model performance on the held-out test set.", 5.8)
para(
    "Extra Trees performed best on all three reported metrics. Compared with raw-price "
    "linear regression, its MAE was approximately 13.3% lower and RMSE approximately "
    "30.4% lower; R-squared increased from 0.3220 to 0.6719. The log-price baseline "
    "performed poorly on this split, including a negative R-squared. The multimodal "
    "model achieved better results than the linear baselines on RMSE and R-squared, but "
    "did not outperform Extra Trees."
)
heading("4.2 Extra Trees feature importance")
add_table(
    ["Rank", "Feature", "Permutation importance (approx. US$ MAE increase)"],
    [
        ["1", "Suburb", "64,307"],
        ["2", "Land size", "43,533"],
        ["3", "Bathrooms", "36,073"],
        ["4", "City", "15,545"],
        ["5", "Floor size", "14,792"],
        ["6", "Bedrooms", "4,700"],
        ["7", "Garages", "2,495"],
        ["8", "Property type", "-9"],
    ],
    [0.6, 2.0, 3.3]
)
para(
    "Suburb and land size were the strongest predictors under this permutation test, "
    "followed by bathrooms. A negative value for property type means that shuffling this "
    "feature slightly improved the test score in these repetitions; it is not evidence "
    "of a software error. Permutation importance describes predictive usefulness for "
    "this model and dataset, not causal effects."
)

# PAGE 5
doc.add_page_break()
page_title("5. Error analysis, limitations and conclusion")
heading("5.1 Residual analysis")
para(
    "For the best model, the test-set MAE was US$106,640.89 and RMSE was US$206,230.97. "
    "Median absolute error was US$51,598.51. Mean residual (actual minus predicted) was "
    "US$18,758.30, while median residual was -US$12,144.65. There were 196 underpredicted "
    "and 284 overpredicted listings. Residuals were strongly right-skewed (skewness 4.09) "
    "and heavy-tailed (kurtosis 32.40). Fifteen test predictions had absolute errors "
    "greater than US$500,000."
)
figure("extra_trees_residuals_vs_predicted.png",
       "Figure 3. Extra Trees residuals against predicted asking prices.", 5.6)
para(
    "The large gap between MAE and RMSE indicates that a relatively small number of large "
    "prediction errors materially affect overall performance. Some of the largest errors "
    "occurred for expensive properties. These listings were not automatically removed "
    "because high asking prices may be genuine market observations."
)
heading("5.2 Limitations")
for item in [
    "The data represent advertised asking prices, not verified completed sale prices.",
    "The sample is concentrated in Harare and may not represent all Zimbabwean markets.",
    "Some location labels are broad or inconsistent, and several property types have few observations.",
    "Missing measurements, especially garages and land size, may limit model accuracy.",
    "Four listings had no usable downloaded image; the multimodal model used zero embeddings and a missing-image indicator.",
    "A single fixed train-test split was used; cross-validation and external validation were not performed.",
    "Listing data and descriptions may contain extraction errors, unreported characteristics or changes over time.",
    "Permutation importance is predictive rather than causal, and the multimodal model did not improve on Extra Trees."
]:
    para("• " + item)
heading("5.3 Conclusion")
para(
    "This study shows that property location and physical characteristics contain useful "
    "information for predicting advertised house prices in the collected Zimbabwean "
    "listings. Extra Trees was the strongest evaluated model, achieving an R-squared of "
    "0.6719 and an MAE of approximately US$106,641 on the held-out test set. Suburb, land "
    "size and bathrooms were the most informative features in its permutation analysis. "
    "However, substantial errors remain, especially for high-value properties. Future "
    "work should improve location standardisation, verify measurements, expand coverage "
    "outside Harare, collect transaction prices where possible, and use repeated "
    "cross-validation and time-based external testing."
)
heading("Data source")
para(
    "Property.co.zw — houses for sale listings, https://www.property.co.zw/. "
    "Dataset collection period: 21–23 November 2026."
)
para(
    "Reproducibility: project scripts, raw and cleaned datasets, model outputs, figures "
    "and environment requirements are maintained in the accompanying project repository."
)

# Keep document metadata useful
doc.core_properties.title = "Zimbabwe House Price Prediction Research Report"
doc.core_properties.subject = "Explaining and predicting advertised house prices in Zimbabwe"
doc.core_properties.author = "Mini Research Project"
doc.core_properties.keywords = "Zimbabwe, house prices, machine learning, Extra Trees, multimodal"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
doc.save(OUTPUT)
print("Report created:", OUTPUT)
print("File size:", OUTPUT.stat().st_size, "bytes")
print("Figures folder:", FIGURES)
