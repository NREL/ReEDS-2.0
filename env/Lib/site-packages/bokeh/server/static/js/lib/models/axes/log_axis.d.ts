import { ContinuousAxis, ContinuousAxisView } from "./continuous_axis";
import { LogTickFormatter } from "../formatters/log_tick_formatter";
import { LogTicker } from "../tickers/log_ticker";
import * as p from "../../core/properties";
export declare class LogAxisView extends ContinuousAxisView {
    model: LogAxis;
}
export declare namespace LogAxis {
    type Attrs = p.AttrsOf<Props>;
    type Props = ContinuousAxis.Props & {};
}
export interface LogAxis extends LogAxis.Attrs {
}
export declare class LogAxis extends ContinuousAxis {
    properties: LogAxis.Props;
    __view_type__: LogAxisView;
    ticker: LogTicker;
    formatter: LogTickFormatter;
    constructor(attrs?: Partial<LogAxis.Attrs>);
}
//# sourceMappingURL=log_axis.d.ts.map