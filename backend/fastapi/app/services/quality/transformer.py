import pandas as pd

MISSING_MARKERS = {"", "NA", "N/A", "NULL", "NONE", "NAN"}


class DataTransformer:

    def __init__(self, df: pd.DataFrame, schema: dict):
        self.df = df
        self.schema = schema

    def normalize_missing_markers(self):
        object_cols = self.df.select_dtypes(include=["object"]).columns

        for col in object_cols:
            stripped = self.df[col].astype("string").str.strip()
            self.df[col] = self.df[col].mask(
                stripped.str.upper().isin(MISSING_MARKERS)
            )

    # --------------------------------------------------
    # DROP HIGHLY CORRUPTED ROWS
    # --------------------------------------------------
    def drop_corrupted_rows(self, threshold: float = 0.7):

        null_ratio = self.df.isna().mean(axis=1)

        self.df = self.df[null_ratio < threshold].copy()

    # --------------------------------------------------
    # NULL HANDLING
    # --------------------------------------------------
    def handle_nulls(self):

        for col, dtype in self.schema.items():

            if col not in self.df.columns:
                continue

            # -----------------------------
            # NUMERIC
            # -----------------------------
            if dtype in ["int", "float"]:

                self.df[col] = pd.to_numeric(
                    self.df[col],
                    errors="coerce"
                )

                median = self.df[col].median()

                if pd.isna(median):
                    median = 0

                self.df[col] = self.df[col].fillna(median)

            # -----------------------------
            # CATEGORICAL
            # -----------------------------
            else:

                self.df[col] = self.df[col].fillna("UNKNOWN")

                self.df[col] = self.df[col].astype(str)

    # --------------------------------------------------
    # TYPE COERCION
    # --------------------------------------------------
    def coerce_types(self):

        for col, dtype in self.schema.items():

            if col not in self.df.columns:
                continue

            try:

                # -----------------------------
                # INT
                # -----------------------------
                if dtype == "int":

                    self.df[col] = pd.to_numeric(
                        self.df[col],
                        errors="coerce"
                    ).astype("Int64")

                # -----------------------------
                # FLOAT
                # -----------------------------
                elif dtype == "float":

                    self.df[col] = pd.to_numeric(
                        self.df[col],
                        errors="coerce"
                    )

                # -----------------------------
                # BOOL
                # -----------------------------
                elif dtype == "bool":

                    self.df[col] = self.df[col].astype(bool)

            except Exception:
                pass

    # --------------------------------------------------
    # NORMALIZE CATEGORICALS
    # --------------------------------------------------
    def normalize_categoricals(self):

        for col, dtype in self.schema.items():

            if col not in self.df.columns:
                continue

            if dtype == "object":

                self.df[col] = (
                    self.df[col]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                )

    # --------------------------------------------------
    # RUN ALL
    # --------------------------------------------------
    def run(self):

        # 0. normalize blank strings and common null tokens before measuring nulls
        self.normalize_missing_markers()

        # 1. remove extremely broken rows
        self.drop_corrupted_rows()

        # 2. fill nulls
        self.handle_nulls()

        # 3. coerce types
        self.coerce_types()

        # 4. normalize strings
        self.normalize_categoricals()

        return self.df
