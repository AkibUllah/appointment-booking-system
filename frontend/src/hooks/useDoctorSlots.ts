import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { addDays, isoDateInDhaka } from '@/lib/format';

export const SLOT_WINDOW_DAYS = 7;

export function useDoctorSlots(doctorId: number | undefined) {
  const from = isoDateInDhaka(new Date());
  const to = addDays(from, SLOT_WINDOW_DAYS - 1);
  const query = useQuery({
    queryKey: ['slots', doctorId, from],
    queryFn: () => api.slots(doctorId!, from, to),
    enabled: doctorId !== undefined,
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
  return { ...query, from, to };
}
