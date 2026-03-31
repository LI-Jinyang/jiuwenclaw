import { useMemo } from 'react';

interface A2UIRendererProps {
  lines?: string[];
}

interface A2UIComponent {
  componentId: string;
  parentId: string | null;
  type: string;
  props?: Record<string, unknown>;
}

const TRUSTED_CATALOG = 'https://a2ui.org/specification/v0_9/basic_catalog.json';
const ALLOWED_TYPES = new Set(['Card', 'Text', 'Button', 'TextField', 'DatePicker', 'Table']);

function isRecord(v: unknown): v is Record<string, unknown> {
  return Boolean(v) && typeof v === 'object' && !Array.isArray(v);
}

export function A2UIRenderer({ lines }: A2UIRendererProps) {
  const parsed = useMemo(() => {
    const components: A2UIComponent[] = [];
    let surfaceOk = false;
    for (const line of lines ?? []) {
      try {
        const obj = JSON.parse(line) as Record<string, unknown>;
        const createSurface = obj.createSurface;
        if (isRecord(createSurface)) {
          surfaceOk =
            createSurface.catalogId === TRUSTED_CATALOG &&
            typeof createSurface.surfaceId === 'string';
          continue;
        }
        const createComponent = obj.createComponent;
        if (!isRecord(createComponent)) continue;
        const type = String(createComponent.type ?? '');
        if (!ALLOWED_TYPES.has(type)) continue;
        components.push({
          componentId: String(createComponent.componentId ?? ''),
          parentId:
            createComponent.parentId == null ? null : String(createComponent.parentId),
          type,
          props: isRecord(createComponent.props) ? createComponent.props : {},
        });
      } catch {
        // ignore malformed lines
      }
    }
    return { surfaceOk, components };
  }, [lines]);

  if (!parsed.surfaceOk) {
    return <div className="text-xs text-text-muted">A2UI surface 无效或 catalog 未通过校验。</div>;
  }

  return (
    <div className="space-y-2">
      {parsed.components.map((component) => (
        <div key={component.componentId} className="rounded-md border border-border p-3 bg-background-subtle">
          <div className="text-xs text-text-muted mb-1">{component.type}</div>
          <pre className="text-xs whitespace-pre-wrap break-words text-text">
            {JSON.stringify(component.props ?? {}, null, 2)}
          </pre>
        </div>
      ))}
      {parsed.components.length === 0 && (
        <div className="text-xs text-text-muted">A2UI 结构已接收，暂无可渲染组件。</div>
      )}
    </div>
  );
}

