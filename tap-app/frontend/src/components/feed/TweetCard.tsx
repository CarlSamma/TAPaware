import { clsx } from 'clsx';
import type { Tweet } from '../../types/tap';

const SOURCE_STYLE: Record<string, string> = {
  our_bot:    'border-l-4 border-[var(--accent-blue)]  bg-[#1c2333]',
  target_bot: 'border-l-4 border-[var(--accent-green)] bg-[#1a2a1a]',
  other_user: 'border-l-4 border-[var(--bg-border)]    bg-[var(--bg-card)]',
};

const SOURCE_LABEL: Record<string, string> = {
  our_bot:    'PROBE',
  target_bot: 'REPLY',
  other_user: 'OTHER',
};

export function TweetCard({ tweet }: { tweet: Tweet }) {
  const ts = new Date(tweet.created_at).toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return (
    <div
      className={clsx(
        'rounded-md p-3 text-sm',
        SOURCE_STYLE[tweet.source] ?? SOURCE_STYLE.other_user
      )}
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="text-[var(--text-muted)] text-xs font-mono">{ts}</span>
          <span className="text-xs text-[var(--accent-blue)]">@{tweet.username}</span>
        </div>
        <span className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
          {SOURCE_LABEL[tweet.source] ?? tweet.source}
        </span>
      </div>
      <p className="text-[var(--text-primary)] leading-relaxed">{tweet.text}</p>
      {tweet.in_reply_to_tweet_id && (
        <p className="text-xs text-[var(--text-muted)] mt-1">
          ↳ reply to {tweet.in_reply_to_tweet_id}
        </p>
      )}
    </div>
  );
}