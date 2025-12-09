library(pheatmap)
library(RColorBrewer)

expr <- read.csv("R_nuclear_protein_zscore.csv", row.names=1, check.names=FALSE)

# Load cluster marker labels
cluster_markers <- read.csv("R_nuclear_protein_labels.csv", row.names=1, check.names=FALSE)
cluster_markers <- cluster_markers[,1]

# Assign colors for marker genes
marker_colors <- brewer.pal(n = length(unique(cluster_markers)), name = "Set3")
names(marker_colors) <- unique(cluster_markers)

# Create annotation data frame for clusters
annotation_row <- data.frame(Marker = cluster_markers)
rownames(annotation_row) <- rownames(expr)

cluster_annotations <- c(
  "0" = "0 CTX Glut",
  "1" = "1 Astro–Epen",
  "2" = "2 Oligo",
  "3" = "3 HY–CNU GABA",
  "4" = "4 Oligo",
  "5" = "5 CTX–HY Astro–Epen",
  "6" = "6 Astro–Epen",
  "7" = "7 Hb Glut",
  "8" = "8 Oligo",
  "9" = "9 CNU–OLF Glut",
  "10" = "10 HY Glut",
  "11" = "11 TH Glut",
  "12" = "12 Astro–Epen",
  "13" = "13 CA1 Glut",
  "14" = "14 DG Glut",
  "15" = "15 CTX–CNU GABA",
  "16" = "16 CTX Glut",
  "17" = "17 Microglia",
  "18" = "18 HY–PIR Glut",
  "19" = "19 TH–HPF Astro-Epen",
  "20" = "20 Epen",
  "21" = "21 CA3 Glut",
  "22" = "22 Oligo",
  "24" = "24 L5 CTX Glut",
  "25" = "25 Oligo",
  "23" = "23 RSC Glut"
)

rownames(expr) <- cluster_annotations[rownames(expr)]
rownames(annotation_row) <- cluster_annotations[rownames(annotation_row)]

# Plot heatmap
pheatmap(
  expr,
  scale = "none",                   
  #cluster_rows = TRUE,
  #cluster_cols = TRUE,
  clustering_distance_rows = "euclidean",
  clustering_distance_cols = "euclidean",  # canberra, manhattan, correlation, euclidean
  clustering_method = "ward.D2", 
  annotation_row = annotation_row,
  #annotation_col = annotation_col,  # <-- add cluster labels on top
  annotation_colors = list(Marker = marker_colors),
  show_rownames = TRUE,
  show_colnames = TRUE,
  fontsize = 8,
  border_color = FALSE,
  cutree_rows = 3, 
  cutree_cols = 4,
  color = colorRampPalette(c("white", "lightyellow", "yellow", "orange","brown"))(100)
)
