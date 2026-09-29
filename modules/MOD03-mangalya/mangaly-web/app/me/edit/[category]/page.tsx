'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';

// Editing lives in the Profile hub's bottom sheets; old links land on the same sheet.
export default function CategoryEditorRedirect() {
  const router = useRouter();
  const { category } = useParams<{ category: string }>();

  useEffect(() => {
    router.replace(`/me?edit=${encodeURIComponent(category)}`);
  }, [category, router]);

  return null;
}
