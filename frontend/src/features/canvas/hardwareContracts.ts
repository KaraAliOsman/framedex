export type HardwareSelection = {
  handle_code?: string | null;
  color_code?: string | null;
  option_codes: string[];
};

export type HardwareResolution = {
  family_name: string;
  class_name: string;
  class_code: string;
  source: string;
  synthetic: boolean;
  width_mm: string;
  height_mm: string;
  exact_leaf_weight_kg: string | null;
  max_leaf_weight_kg: string;
  min_leaf_width_mm: string;
  max_leaf_width_mm: string;
  min_leaf_height_mm: string;
  max_leaf_height_mm: string;
  handle_code: string | null;
  handle_name: string | null;
  handle_color: string | null;
  handle_color_code: string | null;
  handle_height_mm: string | null;
  handle_minimum_mm: string | null;
  handle_maximum_mm: string | null;
  options: string[];
  option_codes: string[];
};

export type HardwareClass = {
  family_name: string;
  class_name: string;
  source: string;
  synthetic: boolean;
  default_handle: string | null;
  handles: {
    code: string;
    name: string;
    default_color: string;
    colors: { code: string; name: string }[];
  }[];
  options: { code: string; name: string; source: string; security_rating?: string | null }[];
};

export type ResolvedHardwareComponent = {
  sku: string;
  name: string;
  qty: string;
  cut_length_mm?: string | null;
  weight_kg?: string | null;
  reason?: string | null;
  source?: string | null;
  machining?: { name: string; positions_mm: string[]; source: string }[];
};
