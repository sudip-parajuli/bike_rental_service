export interface StaffUser { id: number; username: string; full_name: string; email: string; is_superuser: boolean; is_staff: boolean; reminders_enabled: boolean; }
export interface Rental {
  id: number; bike: number; bike_name: string; bike_brand: string; customer_name: string; customer_phone: string;
  customer_email: string; start_date: string; end_date: string; updated_at: string; status: string;
  due_state: string; payment_status: string; total_price: string; paid_amount: string; balance_due: string;
  operations: { notes: string; deposit_amount: string; deposit_returned: boolean; returned_at: string | null };
}
export interface Board { overdue: number; due_today: number; on_rent: number; pickups_today: number; upcoming: number; pending: number; alerts: Rental[]; reminders_enabled: boolean; server_now: string; }
export interface Vehicle { id: number; name: string; brand: string; vehicle_number: string; price_per_day: string; availability_status: boolean; is_approved: boolean; image_url: string | null; }
export const labels: Record<string, string> = { overdue: 'Overdue', due_today: 'Due today', due_soon: 'Due within 24h', on_rent: 'On rent', upcoming: 'Upcoming', pending: 'Pending', completed: 'Returned', cancelled: 'Cancelled' };
export function nepalDate(value = new Date().toISOString()) {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kathmandu', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date(value));
  const get = (key: string) => parts.find(p => p.type === key)?.value;
  return `${get('year')}-${get('month')}-${get('day')}`;
}
export function nepalTime(value: string) { return new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kathmandu', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value)); }
export function displayDate(value: string) { return new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kathmandu', day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value)); }
export function rentalDateTime(date: string, time: string): string {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(time)) throw new Error('Enter a valid date and time (HH:MM).');
  const value = new Date(`${date}T${time}:00+05:45`);
  if (!Number.isFinite(value.getTime()) || nepalDate(value.toISOString()) !== date) throw new Error('Choose a valid calendar date.');
  return value.toISOString();
}
export function money(value: string | number) { return `NPR ${Number(value || 0).toLocaleString('en-NP', { maximumFractionDigits: 2 })}`; }
export function listResults<T>(data: T[] | { results: T[] }): T[] { return Array.isArray(data) ? data : data.results || []; }
export function estimateRentalPrice(rate: number, start: string, end: string, manualDiscount = 0) {
  try {
    const days = Math.round((Date.parse(rentalDateTime(end, '12:00')) - Date.parse(rentalDateTime(start, '12:00'))) / 86400000) + 1;
    if (days < 1 || !Number.isFinite(rate) || !Number.isFinite(manualDiscount) || rate < 0 || manualDiscount < 0) return null;
    const percent = days >= 28 ? .2 : days >= 21 ? .15 : days >= 14 ? .1 : days >= 7 ? .05 : 0;
    const base = rate * days;
    const autoDiscount = Number((base * percent).toFixed(2));
    if (manualDiscount > base - autoDiscount) return null;
    return { days, autoDiscount, total: Number((base - autoDiscount - manualDiscount).toFixed(2)) };
  } catch { return null; }
}
