'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { getBrief } from '@/lib/matchmaker';

import './matchmaker-entry.css';

/* [DEC-V1-031] The way into the AI matchmaker from Discover "For you":
 * an invitation until the member has described who they are looking for,
 * then a quiet line to change it. Renders nothing for someone without a
 * profile of their own (the brief lives on the candidate's profile). */
export default function MatchmakerEntry() {
  const { t } = useTranslation(['discover']);
  const [state, setState] = useState<'hidden' | 'new' | 'saved'>('hidden');

  useEffect(() => {
    let active = true;
    getBrief().then((brief) => {
      if (!active || !brief) return;
      setState(brief.text.trim() || brief.items.length ? 'saved' : 'new');
    });
    return () => {
      active = false;
    };
  }, []);

  if (state === 'hidden') return null;
  const fresh = state === 'new';
  return (
    <Link href="/me/matchmaker" className="mm-entry" prefetch={false}>
      <span className="mm-entry__text">
        <span className="mm-entry__title">
          {t(fresh ? 'discover:matchmaker.entry.title' : 'discover:matchmaker.entry.editTitle')}
        </span>
        <span className="mm-entry__body">
          {t(fresh ? 'discover:matchmaker.entry.body' : 'discover:matchmaker.entry.editBody')}
        </span>
      </span>
      <span className="mm-entry__go" aria-hidden="true">
        {t('discover:matchmaker.entry.open')} →
      </span>
    </Link>
  );
}
