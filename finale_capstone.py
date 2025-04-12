# -*- coding: utf-8 -*-
"""Finale_Capstone.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1draUnpPhtKxl3Jz5haNIuTK-f10B3t_T
"""

# Step 1: Import libraries
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster

url = "https://opendata.arcgis.com/api/v3/datasets/391cca4f364845829abcd5a92093c631_1/downloads/data?format=csv&spatialRefId=4326"
df = pd.read_csv(url)

df.head()

# Step 2: Check for Missing Values
print("Missing values per column:")
print(df.isnull().sum())

#Select Relevant Features
compounds = [
    "CAS307244_PFHxA",
    "CAS307551_PFDoA",
    "CAS335671_PFOA",
    "CAS335762_PFDA",
    "CAS335773_PFDS",
    "CAS355464_PFHxS",
    "CAS375224_PFBA",
    "CAS375735_PFBS",
    "CAS375859_PFHpA",
    "CAS375928_PFHpS",
    "CAS375951_PFNA",
    "CAS376067_PFTeA",
    "CAS754916_PFOSA",
    "CAS1763231_PFOS",
    "CAS2058948_PFUnA",
    "CAS2706903_PFPeA",
    "CAS2706914_PFPeS"
]

#Step 4: Define severity index
severity_index = {
    "CAS335671_PFOA": "High", "CAS1763231_PFOS": "High", "CAS335773_PFDS": "High",
    "CAS375735_PFBS": "Moderate", "CAS355464_PFHxS": "Moderate", "CAS375951_PFNA": "High",
    "CAS307244_PFHxA": "Moderate", "CAS375224_PFBA": "Low", "CAS375859_PFHpA": "Moderate",
    "CAS375928_PFHpS": "Low", "CAS2058948_PFUnA": "Moderate", "CAS335762_PFDA": "High",
    "CAS2706903_PFPeA": "Low", "CAS2706914_PFPeS": "Low", "CAS307551_PFDoA": "Moderate",
    "CAS376067_PFTeA": "Moderate", "CAS754916_PFOSA": "Moderate"
}

df.describe()

df_compounds = df[compounds].copy()
df_compounds.fillna(0, inplace=True)

#Standardize Data
scaler = StandardScaler()
scaled_data = scaler.fit_transform(df_compounds)

full_pca = PCA()
pca_full_result = full_pca.fit_transform(scaled_data)
explained_variance = np.cumsum(full_pca.explained_variance_ratio_)
n_components_95 = np.argmax(explained_variance >= 0.95) + 1

optimal_pca = PCA(n_components=n_components_95)
optimal_pca_result = optimal_pca.fit_transform(scaled_data)

wcss = []
for i in range(1,11):
    kmeans = KMeans(n_clusters=i, init='k-means++',  random_state=42)
    kmeans.fit(scaled_data)
    wcss.append(kmeans.inertia_)
plt.plot(range(1, 11), wcss, marker="o", linestyle="-")
plt.title('the elbow method')
plt.xlabel('number of clusters')
plt.ylabel('wcss')
plt.show()

kmeans = KMeans(n_clusters=3, random_state=42, init = 'k-means++')
cluster = kmeans.fit_predict(optimal_pca_result)

# Top 2 PCA components for plotting
df_plot = pd.DataFrame(pca_full_result[:, :2], columns=["PC1", "PC2"])
df_plot['Cluster'] = clusters

#  Calculate severity score
severity_numeric = {"High": 3, "Moderate": 2, "Low": 1}
compound_weights = pd.Series({c: severity_numeric[severity_index[c]] for c in compounds})
severity_scores = df_compounds.mul(compound_weights).sum(axis=1) / df_compounds.sum(axis=1).replace(0, 1)

# Add severity level
df_plot['Severity_Score'] = severity_scores
df_plot['Severity_Level'] = df_plot['Severity_Score'].apply(
    lambda score: 'High' if score >= 2.5 else 'Moderate' if score >= 1.7 else 'Low'
)

# PCA plot colored by severity
plt.figure(figsize=(10, 7))
for level in ['Low', 'Moderate', 'High']:
    data = df_plot[df_plot['Severity_Level'] == level]
    plt.scatter(data['PC1'], data['PC2'], label=f'Severity: {level}', alpha=0.6)
plt.title("PCA (Top 2 Components) Colored by Severity Level")
plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Step 14: Map results using Folium
df_plot_map = df[['Latitude', 'Longitude']].copy()
df_plot_map['Cluster'] = clusters
df_plot_map['Severity_Score'] = severity_scores
df_plot_map['Severity_Level'] = df_plot['Severity_Level'].values

center_lat = df_plot_map['Latitude'].mean()
center_lon = df_plot_map['Longitude'].mean()
map_severity = folium.Map(location=[center_lat, center_lon], zoom_start=7)

severity_colors = {
    'High': 'red',
    'Moderate': 'orange',
    'Low': 'green'
}

marker_cluster = MarkerCluster().add_to(map_severity)

for idx, row in df_plot_map.iterrows():
    severity = row['Severity_Level']
    folium.CircleMarker(
        location=(row['Latitude'], row['Longitude']),
        radius=5,
        color=severity_colors.get(severity, 'blue'),
        fill=True,
        fill_color=severity_colors.get(severity, 'blue'),
        fill_opacity=0.7,
        popup=folium.Popup(
            f"<b>Severity:</b> {severity}<br><b>Score:</b> {row['Severity_Score']:.2f}<br><b>Cluster:</b> {row['Cluster']}",
            max_width=250
        )
    ).add_to(marker_cluster)

map_severity