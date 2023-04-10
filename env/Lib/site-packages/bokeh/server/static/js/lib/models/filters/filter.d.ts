import { Model } from "../../model";
import { DataSource } from "../sources/data_source";
import { Indices } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace Filter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props;
}
export interface Filter extends Filter.Attrs {
}
export declare abstract class Filter extends Model {
    properties: Filter.Props;
    constructor(attrs?: Partial<Filter.Attrs>);
    abstract compute_indices(source: DataSource): Indices;
}
//# sourceMappingURL=filter.d.ts.map