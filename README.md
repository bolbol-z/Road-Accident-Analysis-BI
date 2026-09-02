# 🚗 Road Accident Analysis BI (France, 2023)

An end-to-end **Business Intelligence** project that analyzes French road accident data from the year **2023**. The project follows a complete data pipeline: it cleans and transforms the raw open-data files, structures them into a document-oriented database, and visualizes the results through an interactive **Streamlit** dashboard powered by **Plotly**.

---

## 🎯 Project Objective

The main objective is to transform raw, messy road-accident records into actionable insights. By combining a reproducible data-cleaning workflow with a database-backed interactive dashboard, the project aims to answer key questions such as:

- Where do the most serious accidents happen?
- When (time of day, month, lighting conditions) do accidents peak?
- Which vehicle categories and road types are most involved?
- What is the demographic and behavioral profile of the users involved?
- How do road surface, infrastructure, and accident circumstances influence outcomes?

The result is a self-serve analytics tool that lets non-technical users explore the data without writing a single query.

---

## 📊 Datasets

The project uses the four French road-accident open-data files for 2023:

| Dataset | Description |
|---------|-------------|
| **Characteristics** (`caract-2023.csv`) | One row per accident — date/time, location (GPS, department, municipality), lighting, weather, collision type, urban/rural context |
| **Locations** (`lieux-2023.csv`) | The road environment for each accident — road category, circulation, surface condition, infrastructure, position on the road |
| **Users** (`usagers-2023.csv`) | Every road user involved — age, sex, seat-belt use, journey purpose, role, and **injury severity** |
| **Vehicles** (`vehicules-2023.csv`) | Every vehicle involved — category, direction, maneuver, number of occupants |

---

## 🔄 Data Workflow

```
Raw CSV data  →  Cleaning & Transformation  →  Structured data  →  MongoDB  →  Interactive Dashboard
```

1. **Raw data** — the four 2023 CSV files.
2. **Cleaning & transformation** — notebooks normalize, clean, and enrich each dataset.
3. **Structured data** — the four datasets are joined and nested into a hierarchical document model.
4. **MongoDB** — the structured documents are stored in a collection.
5. **Dashboard** — the Streamlit app reads from MongoDB and renders the visualizations.

---

## 🧹 Data Cleaning & Transformation

The cleaning notebooks (`analyse et netoyage/`) apply a reproducible cleaning process per dataset:

- **Missing values** — located, then handled by filling, median-imputation, or replacing `-1` flags (which denote "unknown") with meaningful defaults.
- **Duplicates** — detected and removed.
- **String formatting** — standardizing column names, trimming whitespace, and normalizing categorical values.
- **Type coercion** — converting coordinates (`lat` / `long`) and times (`hrmn`) into proper numeric/time formats.
- **Domain enrichment** — deriving new features such as **age** from the birth year and replacing unknown categories with readable labels.
- **Removal of unused columns** — dropping fields with no analytical value.

### Structuring for MongoDB

The relational files are joined into a single **document-oriented** schema:

- Each **accident** is a top-level document (keyed by its accident ID).
- Each accident embeds its list of **vehicles**.
- Each vehicle embeds its list of **users**.
- Each accident also embeds its **locations** (`lieux`) entries.

This eliminates expensive join operations at read time and maps naturally to MongoDB.

---

## 🗄️ Database Structure

- **Database:** `db_accidents_corporels`
- **Collection:** `accidents`

A single document holds one accident and its related entities:

```
accident document
├── accident metadata (date, time, GPS, weather, lighting, ...)
├── vehicules[]         → vehicles involved
│   └── usagers[]       → users in each vehicle
└── lieux[]             → road/location details
```

The four datasets (characteristics, locations, users, vehicles) are related through the accident identifier and nested into this unified structure.

---

## 📈 Dashboard

The interactive **Streamlit** application (`mongo/app.py`) is organized into three main sections.

### 1. Overview
- KPI cards: total accidents, users involved, vehicles involved, serious cases.
- Accidents per month (time series).
- Distribution by lighting conditions.
- Collision type breakdown (pie chart).
- Top vehicle categories (tree map) and user sex distribution.

### 2. Geographic Analysis
- Department filter.
- Interactive map of accident locations (via Mapbox OpenStreetMap).
- Top accident circumstances.
- Road category distribution.
- Infrastructure & situation analysis (sunburst chart).

### 3. Detailed Analysis
Interactive breakdowns per entity:
- **Usagers:** seat-belt usage, journey purpose, age distribution.
- **Véhicules:** vehicle categories (bar / pie / tree map), maneuvers.
- **Lieux:** road categories, circumstances, surface condition, infrastructure.
- **Données Brutes:** browsable raw tables for each entity.

---

## 🔍 Key Analysis Dimensions

- **Severity** of injuries (fatal, hospitalized, light, unharmed)
- **Geography** (department, GPS location)
- **Vehicles** (category, maneuver)
- **Users** (age, sex, seat-belt usage, journey purpose)
- **Lighting** conditions
- **Road conditions** (surface state)
- **Infrastructure** & road categories
- **Temporal** trends (by month)

---

## 🛠️ Technologies

| Technology | Purpose |
|------------|---------|
| **Python** | Core programming language |
| **Pandas & NumPy** | Data cleaning, transformation, and analysis |
| **MongoDB** | Document-oriented database |
| **PyMongo** | Python driver to interface with MongoDB |
| **Streamlit** | Interactive web dashboard framework |
| **Plotly** | Rich, interactive visualizations |

---

## 🚀 Running the Project Locally

### Prerequisites
- Python 3.10+
- A running MongoDB instance containing the `accidents` collection (inserted via the `mongo/conn_mongo.ipynb` notebook).

### 1. Install dependencies

```bash
pip install pandas numpy pymongo streamlit plotly python-dotenv
```

### 2. Load the data into MongoDB

Run the `mongo/conn_mongo.ipynb` notebook. It reads the cleaned CSVs, restructures them into the nested document model, and inserts them into the `accidents` collection.

### 3. Launch the dashboard

```bash
streamlit run mongo/app.py
```

Open the printed local URL (default `http://localhost:8501`) in your browser.

---

## 📁 Project Structure

```
Road-Accident-Analysis-BI/
├── dataset/                       # Raw 2023 CSV data
│   ├── caract-2023.csv           # Accident characteristics
│   ├── lieux-2023.csv            # Locations
│   ├── usagers-2023.csv          # Users
│   └── vehicules-2023.csv        # Vehicles
│
├── analyse et netoyage/           # Cleaning & transformation notebooks
│   ├── caract.ipynb
│   ├── lieux.ipynb
│   ├── usagers.ipynb
│   ├── vehicule.ipynb
│   └── *_nettoye.csv             # Cleaned/transformed outputs
│
├── mongo/                         # Database + dashboard
│   ├── conn_mongo.ipynb          # Restructures data and inserts into MongoDB
│   └── app.py                    # Streamlit BI dashboard
│
└── README.md
```

---

## 📌 Summary

This project demonstrates a complete BI workflow — from messy raw data to a polished, interactive analytics dashboard. It showcases data engineering (cleaning, transformation, and NoSQL modeling), and data visualization (exploratory dashboards), all reproducible and easy to run locally.
