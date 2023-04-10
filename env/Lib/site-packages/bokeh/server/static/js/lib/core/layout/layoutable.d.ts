import { Size, Sizeable, SizeHint, BoxSizing } from "./types";
import { BBox, CoordinateMapper } from "../util/bbox";
export type ExtBoxSizing = BoxSizing & {
    readonly size: Partial<Size>;
};
export declare abstract class Layoutable {
    [Symbol.iterator](): Generator<Layoutable, void, undefined>;
    absolute: boolean;
    position: {
        left: number;
        top: number;
    };
    protected _bbox: BBox;
    protected _inner_bbox: BBox;
    get bbox(): BBox;
    get inner_bbox(): BBox;
    private _sizing;
    get sizing(): ExtBoxSizing;
    private _dirty;
    get visible(): boolean;
    set visible(visible: boolean);
    set_sizing(sizing?: Partial<BoxSizing>): void;
    protected _init(): void;
    protected _set_geometry(outer: BBox, inner: BBox): void;
    set_geometry(outer: BBox, inner?: BBox): void;
    fixup_geometry?(outer: BBox, inner?: BBox): [BBox, BBox?];
    private _handlers;
    on_resize(handler: (outer: BBox, inner: BBox) => void): void;
    is_width_expanding(): boolean;
    is_height_expanding(): boolean;
    apply_aspect(viewport: Size, { width, height }: Size): Size;
    protected abstract _measure(viewport: Sizeable): SizeHint;
    measure(viewport_size: Size): SizeHint;
    compute(viewport?: Partial<Size>): void;
    get xview(): CoordinateMapper;
    get yview(): CoordinateMapper;
    clip_size(size: Size, viewport: Size): Size;
    has_size_changed(): boolean;
}
export declare abstract class ContentLayoutable extends Layoutable {
    protected abstract _content_size(): Sizeable;
    protected _measure(viewport: Sizeable): SizeHint;
}
//# sourceMappingURL=layoutable.d.ts.map