export interface Specialty { id: number; name: string; name_bn: string | null }
export interface Chamber { id: number; name: string; area: string; address: string; phone: string | null }
export interface Doctor {
  id: number;
  name: string;
  name_bn: string | null;
  degrees: string;
  specialty: Specialty;
  chamber: Chamber;
  slot_minutes: number;
  fee_bdt: number;
  experience_years: number;
  is_active: boolean;
}
export interface Slot { start: string; end: string; available: boolean }
export interface DaySlots { date: string; slots: Slot[] }
export interface Patient { id: number; phone: string; name: string }
export type BookingStatus = 'confirmed' | 'cancelled' | 'completed' | 'no_show';
export interface Booking {
  id: number;
  doctor: Doctor;
  patient: Patient;
  chamber: Chamber;
  slot_start: string;
  slot_end: string;
  status: BookingStatus;
  note: string | null;
  reschedule_count: number;
  version: number;
  created_at: string;
  cancelled_at: string | null;
  cancel_reason: string | null;
}
export interface AvailabilityTemplate { id?: number; weekday: number; start_time: string; end_time: string }
export interface AvailabilityException {
  id?: number;
  on_date: string;
  kind: 'leave' | 'extra';
  start_time: string | null;
  end_time: string | null;
  reason: string | null;
}
export interface AdminStats {
  date: string;
  total_bookings: number;
  by_status: Record<BookingStatus, number>;
  today_confirmed: number;
  next_7_days_confirmed: number;
  cancellation_rate: number;
  per_doctor: { doctor_id: number; doctor_name: string; bookings: number }[];
}
export interface ApiError { code: string; message: string }
