import numpy as np

class LayoutAnalyzer:
    def __init__(self):
        pass

    def analyze_spatial_consistency(self, ocr_results):
        """
        Analyzes OCR bounding boxes for spatial anomalies like misalignments
        or irregular vertical/horizontal spacing.
        """
        if not ocr_results or len(ocr_results) < 2:
            return 0.0

        anomaly_score = 0.0
        
        # 1. Check for Vertical Alignment (Heuristic: Most documents are left or right justified)
        # We look at the 'x' coordinates of the left side of bounding boxes
        x_coords = [res['bounding_box'][0][0] for res in ocr_results]
        
        # Calculate standard deviation of x-indices that are "close" to each other
        # (This identifies if text that *should* be aligned is slightly off)
        x_coords.sort()
        diffs = np.diff(x_coords)
        
        # High frequency of very small, non-zero differences indicates "jittery" alignment
        jitter = np.mean([d for d in diffs if 0 < d < 15]) if any(0 < d < 15 for d in diffs) else 0
        anomaly_score += min(jitter / 10.0, 0.5)

        # 2. Irregular Spacing (Heuristic: Paragraphs usually have consistent line height)
        # Analyze vertical distances between nearest neighbors
        y_centers = [np.mean([p[1] for p in res['bounding_box']]) for res in ocr_results]
        y_centers.sort()
        y_diffs = np.diff(y_centers)
        
        if len(y_diffs) > 1:
            spacing_variance = np.var(y_diffs)
            # Normalize variance to a score (arbitrary threshold based on common document layouts)
            norm_spacing = min(spacing_variance / 5000.0, 0.5)
            anomaly_score += norm_spacing

        return float(np.clip(anomaly_score, 0.0, 1.0))

# Singleton
layout_analyzer = LayoutAnalyzer()
