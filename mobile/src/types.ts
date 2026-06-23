// API contract types — mirror the FastAPI Pydantic schemas.

export interface Product {
  id: number;
  barcode: string;
  name: string;
  brand?: string | null;
  category: string;
  image_url?: string | null;
  sugar_g: number;
  sodium_mg: number;
  saturated_fat_g: number;
  protein_g: number;
  fibre_g: number;
  serving_size_g: number;
  price_inr?: number | null;
  trust_tier: string;
}

export interface TranslatedNutrient {
  key: string;
  label: string;
  raw_value: number;
  raw_unit: string;
  plain_value: number;
  plain_unit: string;
  headline: string;
}

export interface Alternative {
  id: number;
  name: string;
  brand?: string | null;
  reason: string;
  hsr_stars: number;
  price_inr?: number | null;
  image_url?: string | null;
}

export interface HSR {
  stars: number;
  final_score: number;
  baseline_points: number;
  modifying_points: number;
  protein_counted: boolean;
}

export interface Nova {
  group: number;
  label: string;
  tag: string;
  rationale: string;
}

export interface ClaimFinding {
  claim: string;
  verdict: "honest" | "misleading" | "unverifiable";
  explanation: string;
}

export interface Claims {
  badge?: string | null;
  findings: ClaimFinding[];
}

export interface Additive {
  code: string;
  plain_english: string;
  possibly_non_veg: boolean;
}

export interface NonVegFlag {
  ingredient: string;
  explanation: string;
}

export interface Ingredients {
  veg_status: "veg" | "non_veg" | "uncertain";
  note: string;
  additives: Additive[];
  non_veg_flags: NonVegFlag[];
}

export interface DetailLayer {
  hsr: HSR;
  nova: Nova;
  claims: Claims;
  ingredients: Ingredients;
}

export interface NutrientProgress {
  key: string;
  label: string;
  consumed: number;
  target: number;
  unit: string;
  pct: number;
  is_goal: boolean;
  headline: string;
}

export interface RecentScan {
  name: string;
  brand?: string | null;
  category: string;
  image_url?: string | null;
  logged_at: string;
  sugar_tsp: number;
  sodium_mg: number;
  protein_g: number;
}

export interface Dashboard {
  date: string;
  primary: NutrientProgress;
  secondary: NutrientProgress[];
  takeaway: string;
  scans_today: number;
  streak: number;
  recent: RecentScan[];
}

export interface ScanResult {
  found: boolean;
  product?: Product | null;
  headline_nutrient?: string | null;
  translation: TranslatedNutrient[];
  alternatives: Alternative[];
  detail?: DetailLayer | null;
  dashboard?: Dashboard | null;
  trust_tier?: string | null;
  needs_photo: boolean;
  message?: string | null;
}

export interface Settings {
  alternatives_priority: "healthier" | "cheaper";
  primary_nutrient: string;
  health_flags: string[];
  target_sugar_tsp?: number | null;
  target_sodium_mg?: number | null;
  target_protein_g?: number | null;
}

export interface TrendPoint {
  date: string;
  value: number;
  pct: number;
}
