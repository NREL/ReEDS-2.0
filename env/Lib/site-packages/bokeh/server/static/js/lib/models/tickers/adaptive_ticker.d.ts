import { ContinuousTicker } from "./continuous_ticker";
import * as p from "../../core/properties";
export declare namespace AdaptiveTicker {
    type Attrs = p.AttrsOf<Props>;
    type Props = ContinuousTicker.Props & {
        base: p.Property<number>;
        mantissas: p.Property<number[]>;
        min_interval: p.Property<number>;
        max_interval: p.Property<number | null>;
    };
}
export interface AdaptiveTicker extends AdaptiveTicker.Attrs {
}
export declare class AdaptiveTicker extends ContinuousTicker {
    properties: AdaptiveTicker.Props;
    constructor(attrs?: Partial<AdaptiveTicker.Attrs>);
    get_min_interval(): number;
    get_max_interval(): number;
    extended_mantissas: number[];
    base_factor: number;
    initialize(): void;
    get_interval(data_low: number, data_high: number, desired_n_ticks: number): number;
}
//# sourceMappingURL=adaptive_ticker.d.ts.map