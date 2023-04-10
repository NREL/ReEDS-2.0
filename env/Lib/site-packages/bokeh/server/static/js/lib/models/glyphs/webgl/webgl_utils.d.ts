import { HatchPattern } from "../../../core/property_mixins";
import { MarkerType } from "../../../core/enums";
export declare const cap_lookup: {
    butt: number;
    round: number;
    square: number;
};
export declare const join_lookup: {
    miter: number;
    round: number;
    bevel: number;
};
export declare function hatch_pattern_to_index(pattern: HatchPattern): number;
export declare function marker_type_to_size_hint(marker_type: MarkerType | "rect"): number;
//# sourceMappingURL=webgl_utils.d.ts.map