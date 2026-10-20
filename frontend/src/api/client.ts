import type {
  AdminStats,
  AvailabilityException,
  AvailabilityTemplate,
  Booking,
  Chamber,
  DaySlots,
  Doctor,
  Patient,
  Specialty,
} from './types';

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api';
const ADMIN_TOKEN = (import.meta.env.VITE_ADMIN_TOKEN as string | undefined) ?? '';

export class ApiRequestError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

async function request<T>(path: string, init: RequestInit = {}, admin = false): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(init.headers as Record<string, string>) };
  if (admin) headers['X-Admin-Token'] = ADMIN_TOKEN;
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const code = typeof body.code === 'string' ? body.code : 'http_error';
    const message =
      typeof body.message === 'string'
        ? body.message
        : Array.isArray(body.detail)
          ? body.detail.map((d: { msg: string }) => d.msg).join('; ')
          : typeof body.detail === 'string'
            ? body.detail
            : `Request failed (${res.status})`;
    throw new ApiRequestError(res.status, code, message);
  }
  return body as T;
}

const qs = (params: Record<string, string | number | boolean | undefined | null>) => {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') sp.set(k, String(v));
  });
  const s = sp.toString();
  return s ? `?${s}` : '';
};

export interface DoctorFilters { q?: string; specialty_id?: number; area?: string; max_fee?: number }

export const api = {
  specialties: () => request<Specialty[]>('/v1/specialties'),
  chambers: () => request<Chamber[]>('/v1/chambers'),
  doctors: (f: DoctorFilters = {}) => request<Doctor[]>(`/v1/doctors${qs({ ...f })}`),
  doctor: (id: number) => request<Doctor>(`/v1/doctors/${id}`),
  slots: (id: number, from: string, to: string) => request<DaySlots[]>(`/v1/doctors/${id}/slots${qs({ from, to })}`),
  registerPatient: (phone: string, name: string) =>
    request<Patient>('/v1/patients', { method: 'POST', body: JSON.stringify({ phone, name }) }),
  createBooking: (doctor_id: number, patient_id: number, slot_start: string, note?: string) =>
    request<Booking>('/v1/bookings', { method: 'POST', body: JSON.stringify({ doctor_id, patient_id, slot_start, note }) }),
  bookingsByPhone: (phone: string) => request<Booking[]>(`/v1/bookings${qs({ phone })}`),
  cancelBooking: (id: number, version: number, reason?: string) =>
    request<Booking>(`/v1/bookings/${id}/cancel`, { method: 'POST', body: JSON.stringify({ version, reason }) }),
  rescheduleBooking: (id: number, version: number, slot_start: string) =>
    request<Booking>(`/v1/bookings/${id}/reschedule`, { method: 'POST', body: JSON.stringify({ version, slot_start }) }),
  admin: {
    stats: () => request<AdminStats>('/v1/admin/stats', {}, true),
    availability: (doctorId: number) => request<AvailabilityTemplate[]>(`/v1/admin/doctors/${doctorId}/availability`, {}, true),
    saveAvailability: (doctorId: number, templates: AvailabilityTemplate[]) =>
      request<AvailabilityTemplate[]>(`/v1/admin/doctors/${doctorId}/availability`, { method: 'PUT', body: JSON.stringify(templates) }, true),
    exceptions: (doctorId: number) => request<AvailabilityException[]>(`/v1/admin/doctors/${doctorId}/exceptions`, {}, true),
    addException: (doctorId: number, e: Omit<AvailabilityException, 'id'>) =>
      request<AvailabilityException>(`/v1/admin/doctors/${doctorId}/exceptions`, { method: 'POST', body: JSON.stringify(e) }, true),
    deleteException: (doctorId: number, id: number) =>
      request<void>(`/v1/admin/doctors/${doctorId}/exceptions/${id}`, { method: 'DELETE' }, true),
  },
};
