import { Ticker, TickSpec } from "./ticker";
import { FactorRange, Factor } from "../ranges/factor_range";
import * as p from "../../core/properties";
export type FactorTickSpec = TickSpec<Factor> & {
    tops: Factor[];
    mids: Factor[];
};
export declare namespace CategoricalTicker {
    type Attrs = p.AttrsOf<Props>;
    type Props = Ticker.Props;
}
export interface CategoricalTicker extends CategoricalTicker.Attrs {
}
export declare class CategoricalTicker extends Ticker {
    properties: CategoricalTicker.Props;
    constructor(attrs?: Partial<CategoricalTicker.Attrs>);
    get_ticks(start: number, end: number, range: FactorRange, _cross_loc: number): FactorTickSpec;
    private _collect;
}
//# sourceMappingURL=categorical_ticker.d.ts.map