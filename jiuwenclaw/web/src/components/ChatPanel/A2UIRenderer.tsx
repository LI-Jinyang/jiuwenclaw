import { useEffect, useMemo, useState } from 'react';
import React from 'react';

interface A2UIRendererProps {
  lines?: string[];
}

interface A2UIComponent {
  componentId: string;
  type: string;
  props?: Record<string, unknown>;
}

const LOCAL_CATALOG = '/a2ui/basic_catalog.v0_9.json';
const REMOTE_CATALOG = 'https://a2ui.org/specification/v0_9/basic_catalog.json';
const DEFAULT_ALLOWED_TYPES = new Set(['Card', 'Row', 'Text', 'Button', 'TextField', 'DatePicker', 'Table']);

interface ParsedSurface {
  surfaceOk: boolean;
  catalogId: string | null;
  components: A2UIComponent[];
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return Boolean(v) && typeof v === 'object' && !Array.isArray(v);
}

function readLiteralString(value: unknown): string {
  if (typeof value === 'string') return value;
  if (isRecord(value) && typeof value.literalString === 'string') {
    return value.literalString;
  }
  return '';
}

function readChildIds(value: unknown): string[] {
  if (typeof value === 'string') return [value];
  if (Array.isArray(value)) return value.filter((item): item is string => typeof item === 'string');
  if (isRecord(value) && Array.isArray(value.explicitList)) {
    return value.explicitList.filter((item): item is string => typeof item === 'string');
  }
  return [];
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
        const updateComponents = obj.updateComponents;
        if (!isRecord(updateComponents)) continue;
        const items = updateComponents.components;
        if (!Array.isArray(items)) continue;
        for (const item of items) {
          if (!isRecord(item)) continue;
          const id = typeof item.id === 'string' ? item.id : '';
          const component = item.component;
          if (!isRecord(component)) continue;
          const entries = Object.entries(component);
          if (entries.length !== 1) continue;
          const [type, props] = entries[0];
          components.push({
            componentId: id || `cmp-${components.length}`,
            type,
            props: isRecord(props) ? props : {},
          });
        }
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
        let types: string[] = [];
        if (Array.isArray(raw)) {
          types = raw
            .map((item) => (isRecord(item) ? item.type : ''))
            .filter((item): item is string => typeof item === 'string' && item.length > 0);
        } else if (isRecord(raw)) {
          types = Object.keys(raw);
        }
        if (types.length > 0) {
          setAllowedTypes(new Set(types));
        }
      })
      .catch(() => {
        // 网络不可达时保留本地默认白名单
      });
  }, [parsed.catalogId, parsed.surfaceOk]);

  const filteredComponents = useMemo(
    () => parsed.components.filter((component) => allowedTypes.has(component.type)),
    [allowedTypes, parsed.components]
  );
  const componentMap = useMemo(
    () => new Map(filteredComponents.map((component) => [component.componentId, component])),
    [filteredComponents]
  );
  const rootId = useMemo(() => {
    if (componentMap.has('root')) return 'root';
    return filteredComponents[0]?.componentId ?? '';
  }, [componentMap, filteredComponents]);

  const renderById = (componentId: string): React.ReactNode => {
    const comp = componentMap.get(componentId);
    if (!comp) return null;
    const props = comp.props ?? {};
    switch (comp.type) {
      case 'Text': {
        const text = readLiteralString(props.text) || JSON.stringify(props);
        return <div className="whitespace-pre-wrap">{text}</div>;
      }
      case 'Button': {
        const label = readLiteralString(props.label) || 'Button';
        return (
          <button
            type="button"
            className="px-3 py-1.5 rounded border border-border bg-secondary text-sm hover:bg-secondary/80"
          >
            {label}
          </button>
        );
      }
      case 'Row': {
        const childIds = readChildIds(props.children);
        return <div className="flex gap-2 flex-wrap">{childIds.map((id) => <React.Fragment key={id}>{renderById(id)}</React.Fragment>)}</div>;
      }
      case 'Column':
      case 'List': {
        const childIds = readChildIds(props.children);
        return <div className="space-y-2">{childIds.map((id) => <React.Fragment key={id}>{renderById(id)}</React.Fragment>)}</div>;
      }
      case 'Card': {
        const title = readLiteralString(props.title);
        const childIds = readChildIds(props.child);
        return (
          <div className="rounded-md border border-border p-3 bg-background-subtle space-y-2">
            {title ? <div className="font-medium">{title}</div> : null}
            {childIds.map((id) => (
              <React.Fragment key={id}>{renderById(id)}</React.Fragment>
            ))}
          </div>
        );
      }
      default:
        return (
          <div className="rounded-md border border-border p-3 bg-background-subtle">
            <div className="text-xs text-text-muted mb-1">{comp.type}</div>
            <pre className="text-xs whitespace-pre-wrap break-words text-text">
              {JSON.stringify(props, null, 2)}
            </pre>
          </div>
        );
    }
  };

  if (!parsed.surfaceOk) {
    return <div className="text-xs text-text-muted">A2UI surface 无效或 catalog 未通过校验。</div>;
  }

  return (
    <div className="space-y-2">
      {rootId ? renderById(rootId) : null}
      {filteredComponents.length === 0 && (
        <div className="text-xs text-text-muted">A2UI 结构已接收，暂无可渲染组件。</div>
      )}
    </div>
  );
}
