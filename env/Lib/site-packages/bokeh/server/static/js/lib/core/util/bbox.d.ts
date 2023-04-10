import { Arrayable, ScreenArray, Rect, Box, Interval, Size } from "../types";
import { equals, Equatable, Comparator } from "./eq";
import * as affine from "./affine";
export declare function empty(): Rect;
export declare function positive_x(): Rect;
export declare function positive_y(): Rect;
export declare function union(a: Rect, b: Rect): Rect;
export type XY<T = number> = {
    x: T;
    y: T;
};
export type LRTB<T = number> = {
    left: T;
    right: T;
    top: T;
    bottom: T;
};
export type Corners<T = number> = {
    top_left: T;
    top_right: T;
    bottom_right: T;
    bottom_left: T;
};
export type HorizontalPosition = {
    left: number;
    width: number;
} | {
    width: number;
    right: number;
} | {
    left: number;
    right: number;
} | {
    hcenter: number;
    width: number;
};
export type VerticalPosition = {
    top: number;
    height: number;
} | {
    height: number;
    bottom: number;
} | {
    top: number;
    bottom: number;
} | {
    vcenter: number;
    height: number;
};
export type Position = HorizontalPosition & VerticalPosition;
export type CoordinateMapper = {
    compute(v: number): number;
    invert(sv: number): number;
    v_compute(vs: Arrayable<number>): ScreenArray;
    v_invert(svs: Arrayable<number>): Arrayable<number>;
    readonly source_range: Interval;
    readonly target_range: Interval;
};
export declare class BBox implements Rect, Equatable {
    readonly x0: number;
    readonly y0: number;
    readonly x1: number;
    readonly y1: number;
    constructor(box?: Rect | Box | Position, correct?: boolean);
    static from_lrtb({ left, right, top, bottom }: LRTB): BBox;
    clone(): BBox;
    equals(that: Rect): boolean;
    [equals](that: this, cmp: Comparator): boolean;
    toString(): string;
    get is_valid(): boolean;
    get is_empty(): boolean;
    get left(): number;
    get top(): number;
    get right(): number;
    get bottom(): number;
    get p0(): XY<number>;
    get p1(): XY<number>;
    get x(): number;
    get y(): number;
    get width(): number;
    get height(): number;
    get size(): Size;
    get rect(): affine.Rect;
    get box(): Box;
    get lrtb(): LRTB;
    get x_range(): Interval;
    get y_range(): Interval;
    get h_range(): Interval;
    get v_range(): Interval;
    get ranges(): [Interval, Interval];
    get aspect(): number;
    get hcenter(): number;
    get vcenter(): number;
    get area(): number;
    round(): BBox;
    relative(): BBox;
    translate(tx: number, ty: number): BBox;
    relativize(x: number, y: number): [number, number];
    contains(x: number, y: number): boolean;
    clip(x: number, y: number): [number, number];
    grow_by(size: number): BBox;
    shrink_by(size: number): BBox;
    union(that: Rect): BBox;
    intersection(that: Rect): BBox | null;
    intersects(that: Rect): boolean;
    private _x_screen?;
    get x_screen(): CoordinateMapper;
    private _y_screen?;
    get y_screen(): CoordinateMapper;
    private _x_view?;
    get x_view(): CoordinateMapper;
    private _y_view?;
    get y_view(): CoordinateMapper;
    get xview(): CoordinateMapper;
    get yview(): CoordinateMapper;
}
//# sourceMappingURL=bbox.d.ts.map