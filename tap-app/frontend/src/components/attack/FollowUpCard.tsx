import { clsx } from 'clsx';
import type { FollowUpOption } from '../../types/tap';

interface Props {
  followup: FollowUpOption;
  selected: string | null;
  onSelect: (choice: 'A' | 'B') => void;
  onPost: () => void;
  loading: boolean;
}

export function FollowUpCard({ followup, selected, onSelect, onPost, loading }: Props) {
  const isASelected = selected === followup.option_a;
  const isBSelected = selected === followup.option_b;

  return (
    <div className="space-y-2">
      {(['A', 'B'] as const).map(choice => {
        const text = choice === 'A' ? followup.option_a : followup.option_b;
        const explanation =
          choice === 'A' ? followup.option_a_explanation : followup.option_b_explanation;
        const strategy =
          choice === 'A' ? followup.option_a_strategy : followup.option_b_strategy;
        const isSelected = choice === 'A' ? isASelected : isBSelected;
        const isRecommended = followup.recommended === choice;

        return (
          <button
            key={choice}
            onClick={() => onSelect(choice)}
            className={clsx(
              'w-full text-left p-3 rounded border text-sm transition-colors',
              isSelected
                ? 'border-[var(--accent-blue)] bg-[#1c2333] text-[var(--text-primary)]'
                : 'border-[var(--bg-border)] bg-[var(--bg-card)] text-[var(--text-muted)] hover:border-[var(--accent-blue)]'
            )}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="font-bold text-[var(--accent-blue)]">Opzione {choice}</span>
              {isRecommended && (
                <span className="text-xs bg-[var(--accent-green)] text-white px-1.5 py-0.5 rounded-full">
                  Raccomandata
                </span>
              )}
              <span className="text-xs text-[var(--text-muted)] ml-auto">{strategy}</span>
            </div>
            <p>{text}</p>
            {explanation && (
              <p className="text-xs mt-1 text-[var(--text-muted)] italic">{explanation}</p>
            )}
          </button>
        );
      })}

      {selected && (
        <button
          onClick={onPost}
          disabled={loading}
          className="w-full py-2 px-4 rounded bg-[var(--accent-green)] text-white text-sm font-medium disabled:opacity-40 hover:opacity-90"
        >
          {loading ? 'Invio...' : '🚀 Invia Probe Selezionato'}
        </button>
      )}
    </div>
  );
}