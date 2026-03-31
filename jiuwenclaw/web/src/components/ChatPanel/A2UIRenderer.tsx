import { useEffect, useMemo, useState } from 'react';

interface A2UIRendererProps {
  lines?: string[];
}

interface A2UIComponent {
  componentId: string;
  parentId: string | null;
  type: string;
  props?: Record<string, unknown>;
}

const LOCAL_CATALOG = '/a2ui/basic_catalog.v0_9.json';
const REMOTE_CATALOG = 'https://a2ui.org/specification/v0_9/basic_catalog.json';
const DEFAULT_ALLOWED_TYPES = new Set(['Card', 'Text', 'Button', 'TextField', 'DatePicker', 'Table']);

interface ParsedSurface {
  surfaceOk: boolean;
  catalogId: string | null;
  components: A2UIComponent[];
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return Boolean(v) && typeof v === 'object' && !Array.isArray(v);
}

export function A2UIRenderer({ lines }: A2UIRendererProps) {
  const parsed = useMemo<ParsedSurface>(() => {
    const components: A2UIComponent[] = [];
    let surfaceOk = false;
    let catalogId: string | null = null;
    for (const line of lines ?? []) {
      try {
        const obj = JSON.parse(line) as Record<string, unknown>;
        const createSurface = obj.createSurface;
        if (isRecord(createSurface)) {
          catalogId = typeof createSurface.catalogId === 'string' ? createSurface.catalogId : null;
          surfaceOk =
            (createSurface.catalogId === LOCAL_CATALOG || createSurface.catalogId === REMOTE_CATALOG) &&
            typeof createSurface.surfaceId === 'string';
          continue;
        }
        const createComponent = obj.createComponent;
        if (!isRecord(createComponent)) continue;
        const type = String(createComponent.type ?? '');
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
    return { surfaceOk, catalogId, components };
  }, [lines]);

  const [allowedTypes, setAllowedTypes] = useState<Set<string>>(DEFAULT_ALLOWED_TYPES);

  useEffect(() => {
    if (!parsed.surfaceOk || !parsed.catalogId) {
      return;
    }
    const target = parsed.catalogId;
    void fetch(target)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: unknown) => {
        if (!isRecord(data)) return;
        const raw = data.components;
        if (!Array.isArray(raw)) return;
        const types = raw
          .map((item) => (isRecord(item) ? item.type : ''))
          .filter((item): item is string => typeof item === 'string' && item.length > 0);
        if (types.length > 0) {
          setAllowedTypes(new Set(types));
        }
      })
      .catch(() => {
        // 网络不可达时保留本地默认白名单
      });
  }, [parsed.catalogId, parsed.surfaceOk]);

  if (!parsed.surfaceOk) {
    return <div className="text-xs text-text-muted">A2UI surface 无效或 catalog 未通过校验。</div>;
  }

  return (
    <div className="space-y-2">
      {parsed.components.filter((component) => allowedTypes.has(component.type)).map((component) => (
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
