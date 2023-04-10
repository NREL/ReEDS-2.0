import { AxisView } from "./axis";
import { LinearAxis } from "./linear_axis";
import { MercatorTickFormatter } from "../formatters/mercator_tick_formatter";
import { MercatorTicker } from "../tickers/mercator_ticker";
import * as p from "../../core/properties";
export declare class MercatorAxisView extends AxisView {
    model: MercatorAxis;
}
export declare namespace MercatorAxis {
    type Attrs = p.AttrsOf<Props>;
    type Props = LinearAxis.Props & {};
}
export interface MercatorAxis extends MercatorAxis.Attrs {
}
export declare class MercatorAxis extends LinearAxis {
    properties: MercatorAxis.Props;
    __view_type__: MercatorAxisView;
    ticker: MercatorTicker;
    formatter: MercatorTickFormatter;
    constructor(attrs?: Partial<MercatorAxis.Attrs>);
}
//# sourceMappingURL=mercator_axis.d.ts.map