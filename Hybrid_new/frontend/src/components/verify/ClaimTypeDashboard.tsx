import { useState } from 'react';

interface ClaimTypeDashboardProps {
  onGenerateProbe: (claimType: string) => void;
}

interface ClaimType {
  id: string;
  name: string;
  status: 'deterministic' | 'conditional';
  icon: 'check' | 'warning';
}

interface ProbePreview {
  claimType: string;
  property: string;
  value: string;
  sha256: string;
  verificationMode: string;
}

const CLAIM_TYPES: ClaimType[] = [
  { id: 'measurement', name: 'MeasurementClaim', status: 'deterministic', icon: 'check' },
  { id: 'citation', name: 'CitationClaim', status: 'deterministic', icon: 'check' },
  { id: 'inference', name: 'InferenceClaim', status: 'conditional', icon: 'warning' },
  { id: 'analogy', name: 'AnalogyClaim', status: 'conditional', icon: 'warning' },
];

const SAMPLE_PROBE: ProbePreview = {
  claimType: 'MeasurementClaim',
  property: 'temperature',
  value: '23.5°C',
  sha256: 'a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8',
  verificationMode: 'Deterministic Verification',
};

export function ClaimTypeDashboard({ onGenerateProbe }: ClaimTypeDashboardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyDigest = async () => {
    await navigator.clipboard.writeText(SAMPLE_PROBE.sha256);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--bg-border)] rounded-lg p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          Claim Types
        </h2>
      </div>

      {/* Claim Types Grid */}
      <div className="grid grid-cols-2 gap-2">
        {CLAIM_TYPES.map((claim) => (
          <div
            key={claim.id}
            className="flex items-center gap-2 p-2 rounded bg-[var(--bg-base)]"
          >
            <span
              className={
                claim.icon === 'check'
                  ? 'text-[var(--accent-green)]'
                  : 'text-[var(--accent-yellow)]'
              }
            >
              {claim.icon === 'check' ? '✅' : '⚠️'}
            </span>
            <div className="flex-1 min-w-0">
              <div className="text-xs text-[var(--text-primary)] truncate">
                {claim.name}
              </div>
              <div
                className={`text-xs ${
                  claim.status === 'deterministic'
                    ? 'text-[var(--accent-green)]'
                    : 'text-[var(--accent-yellow)]'
                }`}
              >
                {claim.status === 'deterministic' ? 'Deterministic' : 'Conditional'}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Probe Preview */}
      <div className="space-y-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          Current Probe Preview
        </span>
        <div className="p-3 rounded bg-[var(--bg-base)] space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-[var(--text-muted)]">Claim Type</span>
            <span className="text-[var(--text-primary)]">{SAMPLE_PROBE.claimType}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-[var(--text-muted)]">Property</span>
            <span className="text-[var(--text-primary)]">{SAMPLE_PROBE.property}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-[var(--text-muted)]">Value</span>
            <span className="text-[var(--accent-blue)]">{SAMPLE_PROBE.value}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-[var(--text-muted)]">SHA-256</span>
            <span className="text-[var(--text-primary)] font-mono">{SAMPLE_PROBE.sha256}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-[var(--text-muted)]">Verification</span>
            <span className="text-[var(--accent-green)]">{SAMPLE_PROBE.verificationMode}</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-2">
        <button
          onClick={() => onGenerateProbe('measurement')}
          className="w-full px-3 py-2 text-xs font-medium rounded bg-[var(--accent-blue)] text-[var(--bg-base)] hover:opacity-90 transition-opacity"
        >
          Genera Measurement Probe
        </button>
        <button
          onClick={() => onGenerateProbe('citation')}
          className="w-full px-3 py-2 text-xs font-medium rounded bg-[var(--accent-green)] text-[var(--bg-base)] hover:opacity-90 transition-opacity"
        >
          Genera Citation Probe
        </button>
        <button
          onClick={handleCopyDigest}
          className="w-full px-3 py-2 text-xs font-medium rounded border border-[var(--bg-border)] text-[var(--text-primary)] hover:bg-[var(--bg-border)] transition-colors"
        >
          {copied ? 'Copiato!' : 'Copia Digest'}
        </button>
      </div>
    </div>
  );
}
