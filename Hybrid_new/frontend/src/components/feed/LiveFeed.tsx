import { useState, useEffect } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { api } from '../../hooks/useApi';
import { TweetCard } from './TweetCard';
import type { Tweet } from '../../types/tap';

export function LiveFeed() {
  const [tweets, setTweets] = useState<Tweet[]>([]);
  const { on } = useWebSocket();

  // Load initial history
  useEffect(() => {
    api.feed(50).then(data => setTweets(data.reverse()));
  }, []);

  // Prepend new tweets from WebSocket
  useEffect(() => {
    const unsub = on('new_tweet', (data) => {
      setTweets(prev => [data as unknown as Tweet, ...prev].slice(0, 200));
    });
    return unsub;
  }, [on]);

  return (
    <div className="flex flex-col gap-2 overflow-y-auto max-h-[calc(100vh-160px)]">
      {tweets.length === 0 && (
        <p className="text-center text-[var(--text-muted)] py-8">
          In attesa di tweet...
        </p>
      )}
      {tweets.map(t => (
        <TweetCard key={t.id} tweet={t} />
      ))}
    </div>
  );
}