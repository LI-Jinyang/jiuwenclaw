import { A2UIRuntimeRenderer } from './A2UIRuntimeRenderer';

interface A2UIRendererProps {
  lines?: string[];
}

/**
 * Compatibility wrapper:
 * keep original import path stable to reduce merge conflicts with upstream branches.
 */
export function A2UIRenderer({ lines }: A2UIRendererProps) {
  return <A2UIRuntimeRenderer lines={lines} />;
}

