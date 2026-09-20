// C:/Users/jasmi/OneDrive/Desktop/THERMOSENTRY-AI/frontend/src/components/events/EventCard.tsx
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { RiskGauge } from '@/components/events/RiskGauge';

export type Event = {
  id: string;
  location: string;
  timestamp: string; // ISO
  riskScore: number; // 0‑100
  classification: 'industrial' | 'vegetation' | 'gasflare' | 'agri' | 'persistent' | 'uncertain';
};

export default function EventCard({ event }: { event: Event }) {
  const riskColor =
    event.riskScore < 25
      ? 'risk-low'
      : event.riskScore < 50
      ? 'risk-mod'
      : event.riskScore < 75
      ? 'risk-high'
      : 'risk-crit';

  const classificationColor = `class-${event.classification}` as const;

  return (
    <Link href={`/events/${event.id}`} className="block">
      <div className="flex items-center gap-4 p-3 bg-surface-2 rounded-lg hover:bg-surface-1 transition-colors">
        <div className="flex-shrink-0 w-12 h-12 bg-surface-1 rounded-full flex items-center justify-center">
          <RiskGauge score={event.riskScore} color={riskColor} size={36} />
        </div>
        <div className="flex-1">
          <h4 className="font-heading text-text-primary">{event.id}</h4>
          <p className="text-sm text-text-muted">{event.location}</p>
          <p className="text-xs text-text-muted">{formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}</p>
        </div>
        <div className={`w-4 h-4 rounded-full bg-${classificationColor}`} title={event.classification} />
      </div>
    </Link>
  );
}
