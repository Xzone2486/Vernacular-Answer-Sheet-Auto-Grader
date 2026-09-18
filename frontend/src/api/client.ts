const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('access_token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
};

const handleResponse = async (response: Response) => {
  if (response.status === 401) {
    // Unauthorized: clear token and redirect to login
    localStorage.removeItem('access_token');
    window.dispatchEvent(new Event('auth:unauthorized'));
    throw new Error('Unauthorized');
  }
  
  if (!response.ok) {
    let errorMessage = response.statusText;
    try {
      const errorData = await response.json();
      if (errorData.detail) errorMessage = errorData.detail;
    } catch {
      // Ignore JSON parse errors
    }
    throw new Error(errorMessage);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
};

export const apiClient = {
  get: async (endpoint: string, params?: Record<string, string | number>) => {
    let url = `${API_BASE_URL}${endpoint}`;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, String(value));
      });
      url += `?${searchParams.toString()}`;
    }

    const response = await fetch(url, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  post: async (endpoint: string, data: any) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  put: async (endpoint: string, data: any) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  delete: async (endpoint: string) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  postForm: async (endpoint: string, formData: FormData) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: getAuthHeaders(), // Don't set Content-Type; browser handles boundary
      body: formData,
    });
    return handleResponse(response);
  },

  uploadUrl: (relativePath: string) => `${API_BASE_URL}/uploads/${relativePath}`,
};
