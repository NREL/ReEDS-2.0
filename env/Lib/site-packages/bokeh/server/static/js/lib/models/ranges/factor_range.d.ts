import { Range } from "./range";
import { PaddingUnits } from "../../core/enums";
import * as p from "../../core/properties";
import { Arrayable, ScreenArray } from "../../core/types";
export type L1Factor = string;
export type L2Factor = [string, string];
export type L3Factor = [string, string, string];
export type Factor = L1Factor | L2Factor | L3Factor;
export type FactorSeq = L1Factor[] | L2Factor[] | L3Factor[];
export declare const Factor: import("../../core/kinds").Kinds.Or<[string, [string, string], [string, string, string]]>;
export declare const FactorSeq: import("../../core/kinds").Kinds.Or<[string[], [string, string][], [string, string, string][]]>;
export type BoxedFactor = [string] | L2Factor | L3Factor;
export type L1Factors = Arrayable<L1Factor>;
export type L2Factors = Arrayable<L2Factor>;
export type L3Factors = Arrayable<L3Factor>;
export type Factors = L1Factors | L2Factors | L3Factors;
export type L1OffsetFactor = [string, number];
export type L2OffsetFactor = [string, string, number];
export type L3OffsetFactor = [string, string, string, number];
export type OffsetFactor = L1OffsetFactor | L2OffsetFactor | L3OffsetFactor;
export type FactorLike = number | Factor | BoxedFactor | OffsetFactor;
export type L1Mapping = Map<string, {
    value: number;
}>;
export type L2Mapping = Map<string, {
    value: number;
    mapping: L1Mapping;
}>;
export type L3Mapping = Map<string, {
    value: number;
    mapping: L2Mapping;
}>;
export type Mapping = L1Mapping | L2Mapping | L3Mapping;
export declare function map_one_level(factors: L1Factor[], padding: number, offset?: number): [L1Mapping, number];
export declare function map_two_levels(factors: L2Factor[], outer_pad: number, factor_pad: number, offset?: number): [L2Mapping, number];
export declare function map_three_levels(factors: L3Factor[], outer_pad: number, inner_pad: number, factor_pad: number, offset?: number): [L3Mapping, number];
export declare namespace FactorRange {
    type Attrs = p.AttrsOf<Props>;
    type Props = Range.Props & {
        factors: p.Property<Factor[]>;
        factor_padding: p.Property<number>;
        subgroup_padding: p.Property<number>;
        group_padding: p.Property<number>;
        range_padding: p.Property<number>;
        range_padding_units: p.Property<PaddingUnits>;
        start: p.Property<number>;
        end: p.Property<number>;
        levels: p.Property<number>;
        mids: p.Property<[string, string][] | null>;
        tops: p.Property<string[] | null>;
    };
}
export interface FactorRange extends FactorRange.Attrs {
}
export declare class FactorRange extends Range {
    properties: FactorRange.Props;
    constructor(attrs?: Partial<FactorRange.Attrs>);
    protected _mapping: Mapping;
    get min(): number;
    get max(): number;
    initialize(): void;
    connect_signals(): void;
    reset(): void;
    protected _lookup(x: BoxedFactor): number;
    synthetic(x: FactorLike): number;
    v_synthetic(xs: Arrayable<number | Factor | [string] | OffsetFactor>): ScreenArray;
    protected _init(silent: boolean): void;
}
//# sourceMappingURL=factor_range.d.ts.map