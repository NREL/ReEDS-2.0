import { HasProps } from "./core/has_props";
import { Class } from "./core/class";
import { ModelEvent, ModelEventType, BokehEventMap } from "./core/bokeh_events";
import * as p from "./core/properties";
import { equals, Comparator } from "./core/util/eq";
import { CallbackLike0 } from "./models/callbacks/callback";
export type ModelSelector<T> = Class<T> | string | {
    type: string;
};
export type ChangeCallback = CallbackLike0<Model>;
export type EventCallback<T extends ModelEvent = ModelEvent> = CallbackLike0<T>;
export type EventCallbackLike<T extends ModelEvent = ModelEvent> = EventCallback<T> | EventCallback<T>["execute"];
export declare namespace Model {
    type Attrs = p.AttrsOf<Props>;
    type Props = HasProps.Props & {
        tags: p.Property<unknown[]>;
        name: p.Property<string | null>;
        js_property_callbacks: p.Property<{
            [key: string]: ChangeCallback[];
        }>;
        js_event_callbacks: p.Property<{
            [key: string]: EventCallback[];
        }>;
        subscribed_events: p.Property<Set<string>>;
        syncable: p.Property<boolean>;
    };
}
export interface Model extends Model.Attrs {
}
export declare class Model extends HasProps {
    properties: Model.Props;
    private _js_callbacks;
    get is_syncable(): boolean;
    [equals](that: this, cmp: Comparator): boolean;
    constructor(attrs?: Partial<Model.Attrs>);
    initialize(): void;
    connect_signals(): void;
    _process_event(event: ModelEvent): void;
    trigger_event(event: ModelEvent): void;
    protected _update_event_callbacks(): void;
    protected _update_property_callbacks(): void;
    protected _doc_attached(): void;
    protected _doc_detached(): void;
    select<T extends HasProps>(selector: ModelSelector<T>): T[];
    select_one<T extends HasProps>(selector: ModelSelector<T>): T | null;
    on_event<T extends ModelEventType>(event: T, callback: EventCallbackLike<BokehEventMap[T]>): void;
    on_event<T extends ModelEvent>(event: Class<T>, callback: EventCallbackLike<T>): void;
}
//# sourceMappingURL=model.d.ts.map