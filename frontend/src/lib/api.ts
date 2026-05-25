import axios from "axios";

const getApiBase = () => {
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
  return `http://${host}:8001/api`;
};

export const API_BASE = getApiBase();

export const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("visionid_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => {
    // If the response is wrapped in a ResponseEnvelope, unwrap it
    if (res.data && typeof res.data === "object" && "success" in res.data) {
      if (res.data.success) {
        res.data = res.data.data;
      }
    }
    return res;
  },
  (err) => {
    // Normalize structured error responses for the frontend
    if (err?.response?.data && typeof err.response.data === "object") {
      const errorObj = err.response.data.error;
      if (errorObj && typeof errorObj === "object") {
        err.response.data.detail = errorObj.message;
        if (errorObj.details && Array.isArray(errorObj.details)) {
          const detailStr = errorObj.details.map((d: any) => `${d.field}: ${d.message}`).join(", ");
          if (detailStr) {
            err.response.data.detail += ` (${detailStr})`;
          }
        }
      }
    }

    if (err?.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("visionid_token");
      localStorage.removeItem("visionid_user");
      if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);


