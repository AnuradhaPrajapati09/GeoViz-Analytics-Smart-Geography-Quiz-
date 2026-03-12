# 🌍 GeoViz Analytics - Smart Geography Quiz
<br>
[🚀 View Live App](https://anuradhaprajapati09-geoviz-analytics-smart-geography-app-sbqhtr.streamlit.app)
<br>
GeoViz Analytics is an interactive web application designed to bridge the gap between data visualization and geographical learning. Built with **Python** and **Streamlit**, it provides users with a platform to explore global data trends and challenge their knowledge via a dynamic quiz system.

## ✨ Key Features
* **Interactive Dashboard:** Visualizes country-level data using **Plotly** for high-quality, interactive maps and charts.
* **Smart Quiz Engine:** A randomized geography quiz that pulls from processed datasets to test user knowledge.
* **Persistent Statistics:** Uses a local **SQLite** database to log user attempts, track scores, and maintain a history of quiz performance.
* **Custom UI:** Enhanced user experience with a tailored `style.css` and a wide-layout Streamlit configuration.

## 🛠️ Tech Stack
* **Frontend:** [Streamlit](https://streamlit.io/)
* **Data Processing:** [Pandas](https://pandas.pydata.org/)
* **Visualization:** [Plotly Express](https://plotly.com/python/plotly-express/)
* **Database:** SQLite (managed via Python's `sqlite3`)
* **Styling:** Custom CSS

## 📁 Project Structure
* `app.py`: The main entry point for the Streamlit application.
* `data_loader.py`: Handles data ingestion and cleaning of geographical datasets.
* `db_manager.py`: Contains the logic for initializing the database and managing user stats.
* `data/`: Directory containing the `countries_cleaned_merged.csv` dataset.
* `style.css`: Custom styles for the app interface.

## 🚀 Getting Started

### Prerequisites
Ensure you have Python installed. You can install the necessary libraries using:
```bash
pip install streamlit pandas plotly
