// Standard API envelope — matches backend APIResponse[T]
export interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
  meta?: PaginationMeta | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details: string[];
  };
}
