import { Model } from "../../model";
import * as p from "../../core/properties";
export type CallbackFn<Obj, Args extends any[], Ret = void> = (obj: Obj, ...args: Args) => Ret;
export type CallbackLike<Obj, Args extends any[], Ret = void> = {
    execute: CallbackFn<Obj, Args, Ret>;
};
export type CallbackLike0<Obj, Ret = void> = CallbackLike<Obj, [], Ret>;
export type CallbackLike1<Obj, Arg, Ret = void> = CallbackLike<Obj, [Arg], Ret>;
export declare namespace Callback {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props;
}
export interface Callback extends Callback.Attrs {
}
export declare abstract class Callback extends Model implements CallbackLike<unknown, any> {
    properties: Callback.Props;
    constructor(attrs?: Partial<Callback.Attrs>);
    abstract execute(cb_obj: unknown, cb_data?: {
        [key: string]: unknown;
    }): unknown;
}
//# sourceMappingURL=callback.d.ts.map