import type { HasProps } from "./has_props";
import { Property } from "./properties";
import { Signal0, Signal, Slot, ISignalable } from "./signaling";
import { BBox } from "./util/bbox";
export type ViewOf<T extends HasProps> = T["__view_type__"];
export type SerializableState = {
    type: string;
    bbox?: BBox;
    children?: SerializableState[];
};
export declare namespace View {
    type Options = {
        model: HasProps;
        parent: View | null;
        owner?: ViewManager;
    };
}
export type IterViews<T extends View = View> = Generator<T, void, undefined>;
export declare class View implements ISignalable {
    readonly removed: Signal0<this>;
    readonly model: HasProps;
    readonly parent: View | null;
    readonly root: View;
    readonly owner: ViewManager;
    protected _ready: Promise<void>;
    get ready(): Promise<void>;
    children(): IterViews;
    protected _has_finished: boolean;
    connect<Args, Sender extends object>(signal: Signal<Args, Sender>, slot: Slot<Args, Sender>): boolean;
    disconnect<Args, Sender extends object>(signal: Signal<Args, Sender>, slot: Slot<Args, Sender>): boolean;
    constructor(options: View.Options);
    initialize(): void;
    lazy_initialize(): Promise<void>;
    protected _removed: boolean;
    remove(): void;
    toString(): string;
    serializable_state(): SerializableState;
    get is_root(): boolean;
    has_finished(): boolean;
    get is_idle(): boolean;
    connect_signals(): void;
    disconnect_signals(): void;
    on_change(properties: Property<unknown> | Property<unknown>[], fn: () => void): void;
    cursor(_sx: number, _sy: number): string | null;
    on_hit?(sx: number, sy: number): boolean;
    private _idle_notified;
    notify_finished(): void;
}
export declare class ViewManager {
    readonly roots: Set<View>;
    constructor(roots?: View[]);
    get<T extends HasProps>(model: T): ViewOf<T> | null;
    add(view: View): void;
    delete(view: View): void;
    [Symbol.iterator](): IterViews;
    query(fn: (view: View) => boolean): IterViews;
    find<T extends HasProps>(model: T): IterViews<ViewOf<T>>;
    get_one<T extends HasProps>(model: T): ViewOf<T>;
    find_one<T extends HasProps>(model: T): ViewOf<T> | null;
    find_all<T extends HasProps>(model: T): ViewOf<T>[];
}
//# sourceMappingURL=view.d.ts.map