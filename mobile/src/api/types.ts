export type ItemState =
  | 'matched'
  | 'needs_review'
  | 'unmatched'
  | 'unreadable'
  | 'extraction_failed';

export type PipelineStatus =
  | 'success'
  | 'partial_success'
  | 'no_books_detected'
  | 'failed';

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

export interface VLMExtractionData {
  title: string | null;
  author: string | null;
  readability: string;
  status: string;
  error_reason: string | null;
}

export interface CatalogCandidate {
  catalog_id: string;
  work_id?: string;
  title: string;
  author: string;
  edition?: string;
  publication_year?: string;
  score: number;
  title_score?: number;
  author_score?: number;
}

export interface MatchData {
  state: 'matched' | 'needs_review' | 'unmatched';
  match_score: number;
  confidence: number;
  best_candidate: CatalogCandidate | null;
  alternatives: CatalogCandidate[];
}

export interface AnalysisItem {
  item_id: string;
  bbox: BoundingBox;
  detector_confidence: number;
  state: ItemState;
  extraction: VLMExtractionData;
  match: MatchData | null;
}

export interface PipelineSummary {
  detections: number;
  matched: number;
  needs_review: number;
  unmatched: number;
  unreadable: number;
  extraction_failed: number;
}

export interface PipelineMetrics {
  detection_ms: number;
  crop_prep_ms: number;
  vlm_ms: number;
  matching_ms: number;
  total_ms: number;
  api_requests: number;
  api_cost_usd: number | null;
}

export interface AnalyzeResponse {
  status: PipelineStatus;
  summary: PipelineSummary;
  items: AnalysisItem[];
  metrics: PipelineMetrics;
  warnings: string[];
}

export interface MatchCorrectionResponse {
  state: 'matched' | 'needs_review' | 'unmatched';
  match_score: number;
  runner_up_score: number;
  margin: number;
  confidence: number;
  best_candidate: CatalogCandidate | null;
  alternatives: CatalogCandidate[];
  signals: Record<string, any>;
}

export interface LibraryBook {
  id: number;
  catalog_id: string | null;
  confirmed_title: string;
  confirmed_author: string | null;
  edition: string | null;
  source_match_confidence: number | null;
  added_at: string;
}

export interface LibraryListResponse {
  count: number;
  books: LibraryBook[];
}

export interface LibraryAddRequestItem {
  catalog_id?: string | null;
  confirmed_title: string;
  confirmed_author?: string | null;
  edition?: string | null;
  source_match_confidence?: number | null;
}

export interface LibraryAddResponse {
  status: string;
  added_count: number;
  duplicate_count: number;
  books: LibraryBook[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}
