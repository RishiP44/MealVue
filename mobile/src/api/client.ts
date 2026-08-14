import {
  AnalyzeResponse,
  MatchCorrectionResponse,
  LibraryListResponse,
  LibraryAddRequestItem,
  LibraryAddResponse,
  ApiError,
} from './types';

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const CLIENT_TIMEOUT_MS = 60000; // 60s timeout for complete multi-crop hosted VLM pipeline

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async requestWithTimeout(
    url: string,
    options: RequestInit = {},
    timeoutMs: number = CLIENT_TIMEOUT_MS
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      return response;
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw new Error('Analysis timed out. The server took longer than 60 seconds to process the shelf.');
      }
      if (err.message && (err.message.includes('fetch') || err.message.includes('Network') || err.name === 'TypeError')) {
        throw new Error("We couldn't connect to Shelfie. Please check that the server is running and try again.");
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Health check probe
   */
  async checkHealth(): Promise<boolean> {
    try {
      const resp = await this.requestWithTimeout(`${this.baseUrl}/api/health/`, {}, 5000);
      if (!resp.ok) return false;
      const data = await resp.json();
      return data?.status === 'ok';
    } catch {
      return false;
    }
  }

  /**
   * Upload image to analyze bookshelf: Detector -> VLM -> Matcher
   */
  async analyzeShelf(
    imageUri: string,
    mimeType: string = 'image/jpeg',
    fileName: string = 'shelf.jpg'
  ): Promise<AnalyzeResponse> {
    const formData = new FormData();

    // React Native FormData object convention
    if (typeof window === 'undefined' || !imageUri.startsWith('blob:')) {
      // Native (iOS/Android) or standard URI
      formData.append('image', {
        uri: imageUri,
        type: mimeType,
        name: fileName,
      } as any);
    } else {
      // Web blob support
      const blob = await (await fetch(imageUri)).blob();
      formData.append('image', blob, fileName);
    }

    const response = await this.requestWithTimeout(`${this.baseUrl}/api/analyze/`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = `Server returned status ${response.status}`;
      try {
        const errorData: ApiError = await response.json();
        if (errorData?.error?.message) {
          errorMsg = errorData.error.message;
        }
      } catch {
        // Fall back to default status string
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  }

  /**
   * Rerun deterministic matcher on user-corrected title/author
   */
  async matchBook(
    title?: string | null,
    author?: string | null
  ): Promise<MatchCorrectionResponse> {
    const response = await this.requestWithTimeout(`${this.baseUrl}/api/match/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: title || '',
        author: author || '',
      }),
    });

    if (!response.ok) {
      let errorMsg = `Match correction failed (${response.status})`;
      try {
        const err: ApiError = await response.json();
        if (err?.error?.message) {
          errorMsg = err.error.message;
        }
      } catch {
        // Keep default
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  }

  /**
   * Retrieve all confirmed personal library books
   */
  async getLibrary(): Promise<LibraryListResponse> {
    const response = await this.requestWithTimeout(`${this.baseUrl}/api/library/`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to load personal library (${response.status})`);
    }

    return await response.json();
  }

  /**
   * Persist confirmed books to SQLite library
   */
  async addBooks(books: LibraryAddRequestItem[]): Promise<LibraryAddResponse> {
    const response = await this.requestWithTimeout(`${this.baseUrl}/api/library/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ books }),
    });

    if (!response.ok) {
      let errorMsg = `Failed to save books (${response.status})`;
      try {
        const err: ApiError = await response.json();
        if (err?.error?.message) {
          errorMsg = err.error.message;
        }
      } catch {
        // Keep default
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  }
}

export const apiClient = new ApiClient();
