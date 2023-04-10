import { Arrayable, Data } from "./types";
import { NDArray } from "./util/ndarray";
import { Slice } from "./util/slice";
export declare function stream_to_column(col: Arrayable, new_col: Arrayable, rollover?: number): Arrayable;
export declare function slice(ind: number | Slice, length: number): [number, number, number];
export type Patch<T> = [number, T] | [[number, number | Slice] | [number, number | Slice, number | Slice], T[]] | [Slice, T[]];
export type PatchSet<T> = {
    [key: string]: Patch<T>[];
};
export declare function patch_to_column<T>(col: NDArray | NDArray[], patch: Patch<T>[]): Set<number>;
export declare function stream_to_columns(data: Data, new_data: Data, rollover?: number): void;
export declare function patch_to_columns(data: Data, patches: PatchSet<unknown>): Set<number>;
//# sourceMappingURL=patching.d.ts.map