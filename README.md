# 📈 Advanced Tafel Extrapolation and Polarization Fitting App

A sophisticated Streamlit application for electrochemical polarization-curve analysis, Tafel extrapolation, and adaptive global fitting of LSV / potentiodynamic polarization data.

The app supports **single-file fitting**, **multi-file batch fitting**, and **folder-based batch processing**, with selectable **anodic**, **cathodic**, or **auto-detected** scan modes.

---

## ✨ Key Features

### 🔬 Electrochemical Analysis

- Classical Tafel extrapolation
- Adaptive nonlinear global polarization fitting
- Hybrid fitting workflow:
  - global fit for robust curve representation
  - Tafel extrapolation for final corrosion parameters
- Automatic \(E_{corr}\) detection
- Automatic Tafel-window search
- Manual Tafel-window configuration
- Passive-region detection
- Transpassive / breakdown onset detection
- Current or current-density output
- Support for anodic and cathodic scans

---

### 📁 Processing Modes

The app supports:

1. **Single uploaded file**
2. **Multiple uploaded files**
3. **Batch folder processing**

Batch processing can be filtered by folder name, for example:

- folders containing `(Anodic)`
- folders containing `(Cathodic)`
- custom folder keyword

---

### 📊 Outputs

For each fitted curve, the app provides:

- \(E_{corr}\), observed and fitted
- \(I_{corr}\) or \(i_{corr}\)
- anodic Tafel slope \(b_a\)
- cathodic Tafel slope \(b_c\)
- passive potential \(E_{pp}\)
- transpassive / breakdown potential \(E_b\), if detected
- global fit \(R^2\)
- global fit RMSE
- fit diagnostics
- processed data table
- dense fitted curve
- interactive Plotly visualization

---

### ⬇️ Downloadable Results

The app allows downloading:

- summary JSON
- processed CSV
- dense fit CSV
- diagnostics JSON
- batch summary CSV
- batch summary Excel

---

## 🧱 Project Structure

Recommended folder structure:

```text
tafel_extrapolation_app/
│
├── app.py
├── requirements.txt
├── README.md
│
├── tafel_core/
│   ├── __init__.py
│   ├── config.py
│   ├── data_io.py
│   ├── preprocessing.py
│   ├── math_utils.py
│   ├── detection.py
│   ├── classical_tafel.py
│   ├── global_model.py
│   ├── fitting.py
│   ├── plotting.py
│   ├── reporting.py
│   └── validation.py
│
└── outputs/
```

---

## ⚙️ Installation

### 1. Clone or copy the project

Create a local project directory:

```bash
mkdir tafel_extrapolation_app
cd tafel_extrapolation_app
```

Place the following files inside the project:

```text
app.py
requirements.txt
README.md
tafel_core/
```

---

### 2. Create a Python environment

Recommended:

```bash
python -m venv .venv
```

Activate it.

#### Windows PowerShell

```bash
.venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```bash
.venv\Scripts\activate.bat
```

#### Linux / macOS

```bash
source .venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 📦 Requirements

The required Python packages are:

```text
streamlit
numpy
pandas
scipy
matplotlib
plotly
openpyxl
xlsxwriter
kaleido
```

A typical `requirements.txt` is:

```text
streamlit
numpy
pandas
scipy
matplotlib
plotly
openpyxl
xlsxwriter
kaleido
```

---

## ▶️ Running the App

From the project root directory, run:

```bash
streamlit run app.py
```

The app will open in your browser.

If it does not open automatically, Streamlit will print a local URL such as:

```text
http://localhost:8501
```

Open that address manually in your browser.

---

## 📄 Input Data Format

The app expects polarization data in `.xlsx`, `.xls`, or `.csv` format.

By default, the expected columns are:

```text
WE(1).Potential (V)
WE(1).Current (A)
```

These can be changed in the Streamlit sidebar.

---

## 📊 Example Input Table

| WE(1).Potential (V) | WE(1).Current (A) |
|---:|---:|
| -0.500 | -1.20E-04 |
| -0.495 | -1.11E-04 |
| -0.490 | -1.03E-04 |
| ... | ... |
| 0.300 | 2.40E-05 |

---

## 🧭 App Workflow

### 1. Select Processing Mode

In the sidebar, choose one of:

```text
Single uploaded file
Multiple uploaded files
Batch folder
```

---

### 2. Select Scan Fitting Mode

Choose:

```text
Auto-detect
Anodic scan
Cathodic scan
```

#### Auto-detect

The app determines scan direction from the raw potential sequence.

#### Anodic scan

Forces the fitting engine to treat the data as an anodic scan.

#### Cathodic scan

Forces the fitting engine to treat the data as a cathodic scan.

---

### 3. Select Fit Strategy

Choose one of:

```text
Hybrid: global + Tafel extrapolation
Classical Tafel only
Global model only
```

#### Hybrid Mode

Recommended default.

The app first performs an adaptive global fit, then performs Tafel extrapolation using the globally estimated \(E_{corr}\).

#### Classical Tafel Only

Uses direct Tafel-line extrapolation without nonlinear global fitting.

#### Global Model Only

Uses the nonlinear global model as the main fit source.

---

### 4. Configure Data Columns

Default:

```text
Potential column: WE(1).Potential (V)
Current column:   WE(1).Current (A)
```

Change these if your input file uses different column names.

---

### 5. Optional Area Normalization

If you enable electrode area normalization, the app converts current to current density:

\[
i = \frac{I}{A}
\]

where:

- \(I\) = measured current in A
- \(A\) = electrode area in cm²
- \(i\) = current density in A/cm²

If no area is provided, all results are reported as raw current in A.

---

### 6. Configure Tafel Windows

The app supports automatic Tafel-window detection and manual relative windows.

Manual windows are defined relative to \(E_{corr}\):

```text
Anodic min from Ecorr / V
Anodic max from Ecorr / V
Cathodic min from Ecorr / V
Cathodic max from Ecorr / V
```

Example:

```text
Anodic:   Ecorr + 0.015 V to Ecorr + 0.028 V
Cathodic: Ecorr - 0.045 V to Ecorr - 0.015 V
```

---

### 7. Configure Physical Bounds

The app constrains Tafel slopes to physically meaningful ranges.

Default bounds:

```text
ba min = 0.030 V/dec
ba max = 0.300 V/dec
bc min = 0.030 V/dec
bc max = 0.450 V/dec
```

These can be adjusted in the sidebar.

---

### 8. Run Fit

Click:

```text
Run single fit
```

or:

```text
Run uploaded-file batch fit
```

or:

```text
Run folder batch fit
```

depending on the selected processing mode.

---

## 📁 Batch Folder Mode

Batch folder mode is intended for local or server environments where Streamlit has access to the filesystem.

Example root folder:

```text
C:\Users\USERNAME\OneDrive - Schaeffler\Electrolyzer_EC
```

Target filename:

```text
lsv.xlsx
```

Optional folder filters:

```text
No filter
Only folders containing (Anodic)
Only folders containing (Cathodic)
Custom keyword
```

Example:

If your files are organized like this:

```text
Electrolyzer_EC/
│
├── Sample_01_(Anodic)/
│   └── lsv.xlsx
│
├── Sample_01_(Cathodic)/
│   └── lsv.xlsx
│
├── Sample_02_(Anodic)/
│   └── lsv.xlsx
│
└── Sample_02_(Cathodic)/
    └── lsv.xlsx
```

Then select:

```text
Only folders containing (Cathodic)
```

to process only cathodic scans.

---

## 📈 Main Results

The app reports the following parameters.

### \(E_{corr}\)

Corrosion potential.

The app reports:

```text
Ecorr observed
Ecorr global
Ecorr final
```

### \(I_{corr}\) or \(i_{corr}\)

Corrosion current or current density.

If electrode area is provided:

```text
i_corr in A/cm²
```

Otherwise:

```text
I_corr in A
```

### \(b_a\)

Anodic Tafel slope:

\[
b_a = \frac{1}{m_a}
\]

where \(m_a\) is the slope of the anodic branch in:

\[
\log_{10}|I| \text{ vs } E
\]

### \(b_c\)

Cathodic Tafel slope:

\[
b_c = \left|\frac{1}{m_c}\right|
\]

where \(m_c\) is the slope of the cathodic branch.

### \(E_{pp}\)

Estimated passive potential or passivation transition potential.

### \(E_b\)

Estimated breakdown or transpassive onset potential, if detected.

---

## 🧪 Fit Diagnostics

The diagnostics tab contains:

- optimizer success flag
- optimizer message
- optimizer cost
- number of function evaluations
- fitted parameter vector
- selected configuration
- Tafel-window information
- Tafel-line quality metrics

---

## ⚠️ Quality Flags

The app automatically displays warnings for cases such as:

- unreliable Tafel-line intersection
- passive-dominated curve
- low global fit \(R^2\)
- \(b_a\) outside typical bounds
- \(b_c\) outside typical bounds
- non-positive \(I_{corr}\)
- insufficient Tafel points

These warnings are intended to support scientific review and should not replace expert judgment.

---

## 🧠 Scientific Notes

### Tafel Extrapolation Assumption

Tafel extrapolation is meaningful only when the anodic and cathodic branches contain activation-controlled linear regions.

If the curve is passive-dominated, especially for stainless steels or passivating alloys, the anodic branch may not represent a true metal-dissolution Tafel region.

---

### Passive-Dominated Curves

For passive materials, the anodic current may quickly transition into a passive plateau.

In such cases:

- \(b_a\) may be poorly defined
- \(I_{corr}\) may rely more strongly on cathodic extrapolation
- interpretation should be done carefully

---

### Current vs Current Density

If the area is not supplied, the app reports raw current:

\[
I_{corr} \; [A]
\]

If the area is supplied, the app reports current density:

\[
i_{corr} \; [A/cm^2]
\]

---

## 🧮 Fit Strategies Explained

### Classical Tafel Only

This mode performs direct linear fitting on selected anodic and cathodic Tafel windows.

Advantages:

- simple
- transparent
- fast

Limitations:

- sensitive to window selection
- unreliable for passive-dominated curves
- less robust against noisy data

---

### Global Model Only

This mode fits a nonlinear polarization model to the full curve.

Advantages:

- robust full-curve representation
- useful for passive/transpassive behavior
- can handle complex curve shapes

Limitations:

- more parameters
- requires constraints
- may not always correspond directly to classical Tafel extrapolation

---

### Hybrid Mode

This is the recommended mode.

It combines:

1. global fit for robust estimation of curve behavior
2. Tafel-line extraction for corrosion parameters

Advantages:

- more robust than classical fitting alone
- still reports conventional Tafel parameters
- useful for both active and passive systems

---

## 🔍 Troubleshooting

### App does not start

Check that dependencies are installed:

```bash
pip install -r requirements.txt
```

Then run:

```bash
streamlit run app.py
```

---

### Missing column error

Example error:

```text
Missing potential column: WE(1).Potential (V)
```

Solution:

Check the exact column names in your Excel or CSV file and update the sidebar fields.

---

### Excel file cannot be read

Install Excel dependencies:

```bash
pip install openpyxl xlrd
```

For `.xlsx`, `openpyxl` is required.

For older `.xls`, `xlrd` may be required.

---

### Batch folder does not find files

Check:

1. The root folder path exists.
2. The target filename is correct.
3. Folder filter is not too restrictive.
4. Streamlit has permission to access the folder.
5. Network drives are mounted and accessible.

---

### Fit fails or gives unrealistic values

Try:

- using manual Tafel windows
- disabling automatic Tafel search
- using hybrid mode
- increasing max optimizer evaluations
- checking the scan mode
- checking whether current sign convention is correct
- removing noisy outliers
- verifying electrode area

---

### Plot appears empty

Check:

- input file contains valid numeric values
- potential and current columns are correct
- current is not entirely zero
- there are enough data points

---

## 🧪 Recommended Validation Procedure

Before using the app for production analysis:

1. Test with one known anodic scan.
2. Test with one known cathodic scan.
3. Compare \(E_{corr}\), \(I_{corr}\), \(b_a\), and \(b_c\) with manual analysis.
4. Test automatic scan detection.
5. Test manual scan override.
6. Test automatic Tafel-window search.
7. Test manual Tafel-window settings.
8. Test batch processing on a small folder.
9. Review all quality flags.
10. Confirm downloaded summaries match displayed results.

---

## 🧾 Output Columns

A typical summary contains:

```text
file_name
scan_direction
fit_strategy
result_source
Ecorr_observed_V
Ecorr_detection_method
Ecorr_global_V
Ecorr_final_V
Icorr_abs
current_unit
ba_V_dec
bc_V_dec
ba_initial_guess
bc_initial_guess
passive_dominated
Epp_V
transpassive_detected
Eb_V
R2_log_global
RMSE_log_global
tafel_ok
tafel_reason
tafel_auto_window_used
kpass_V
ktrans_V
cpass
local_corr_amplitude
local_corr_shift_V
local_corr_width_V
```

---

## 📤 Exported Files

For each individual fit, the app can export:

```text
<file_name>_summary.json
<file_name>_processed.csv
<file_name>_dense_fit.csv
<file_name>_diagnostics.json
```

For batch mode:

```text
batch_fit_summary.csv
batch_fit_summary.xlsx
```

---

## 🧩 Future Improvements

Potential future features:

- manual interactive Tafel-window selection on the plot
- automatic outlier detection
- replicate grouping
- statistical confidence intervals
- bootstrap uncertainty analysis
- PDF report generation
- ZIP export of all outputs
- database export
- comparison dashboard for batches
- overlay plot of multiple samples
- corrosion-rate calculation
- equivalent weight and density input
- Stern-Geary corrosion-rate conversion
- project/session saving

---

## 🔐 Notes for Schaeffler / Internal Use

If the app is deployed in an internal environment:

- ensure that file paths are accessible from the Streamlit server
- avoid hard-coded local user paths in production
- prefer uploaded-file mode for web deployment
- validate results against accepted electrochemical analysis procedures
- document default parameter settings for reproducibility

---

## 📌 Version

Initial advanced Streamlit architecture:

```text
Version: 0.1.0
```

---

## 👤 Maintainer

Developed for advanced electrochemical polarization analysis and Tafel extrapolation workflows.

Recommended ownership:

```text
Data Science / Electrochemistry / Materials Engineering
```

---

## ⚠️ Disclaimer

This app provides computational support for Tafel extrapolation and polarization-curve fitting. Results must be interpreted by qualified users with electrochemical expertise.

The software does not replace scientific judgment, experimental validation, or domain-specific corrosion analysis standards.
