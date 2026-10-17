"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// mock-api/actions/upsertSyntheticContact.ts
var upsertSyntheticContact_exports = {};
__export(upsertSyntheticContact_exports, {
  action: () => action,
  default: () => upsertSyntheticContact_default
});
module.exports = __toCommonJS(upsertSyntheticContact_exports);
var z = __toESM(require("zod"), 1);
var input = z.object({
  tenant_id: z.string().endsWith(".invalid"),
  external_id: z.string(),
  email: z.string().email().endsWith(".invalid")
});
var action = {
  type: "action",
  description: "Compile-only synthetic contact connector; never executed by O06",
  version: "1.0.0",
  endpoint: {
    method: "POST",
    path: "/o06/contacts",
    group: "O06 Synthetic"
  },
  input,
  output: z.object({
    external_id: z.string()
  }),
  exec: async (nango, value) => {
    const response = await nango.proxy({
      method: "POST",
      endpoint: "/contacts",
      data: value
    });
    return {
      external_id: String(response.data.external_id)
    };
  }
};
var upsertSyntheticContact_default = action;
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  action
});
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsibW9jay1hcGkvYWN0aW9ucy91cHNlcnRTeW50aGV0aWNDb250YWN0LnRzIl0sCiAgInNvdXJjZXNDb250ZW50IjogWyJpbXBvcnQgeyBjcmVhdGVBY3Rpb24gfSBmcm9tICduYW5nbyc7XG5pbXBvcnQgKiBhcyB6IGZyb20gJ3pvZCc7XG5jb25zdCBpbnB1dCA9IHoub2JqZWN0KHtcbiAgdGVuYW50X2lkOiB6LnN0cmluZygpLmVuZHNXaXRoKCcuaW52YWxpZCcpLFxuICBleHRlcm5hbF9pZDogei5zdHJpbmcoKSxcbiAgZW1haWw6IHouc3RyaW5nKCkuZW1haWwoKS5lbmRzV2l0aCgnLmludmFsaWQnKVxufSk7XG5leHBvcnQgY29uc3QgYWN0aW9uID0ge1xuICB0eXBlOiBcImFjdGlvblwiLFxuICBkZXNjcmlwdGlvbjogJ0NvbXBpbGUtb25seSBzeW50aGV0aWMgY29udGFjdCBjb25uZWN0b3I7IG5ldmVyIGV4ZWN1dGVkIGJ5IE8wNicsXG4gIHZlcnNpb246ICcxLjAuMCcsXG4gIGVuZHBvaW50OiB7XG4gICAgbWV0aG9kOiAnUE9TVCcsXG4gICAgcGF0aDogJy9vMDYvY29udGFjdHMnLFxuICAgIGdyb3VwOiAnTzA2IFN5bnRoZXRpYydcbiAgfSxcbiAgaW5wdXQsXG4gIG91dHB1dDogei5vYmplY3Qoe1xuICAgIGV4dGVybmFsX2lkOiB6LnN0cmluZygpXG4gIH0pLFxuICBleGVjOiBhc3luYyAobmFuZ28sIHZhbHVlKSA9PiB7XG4gICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBuYW5nby5wcm94eSh7XG4gICAgICBtZXRob2Q6ICdQT1NUJyxcbiAgICAgIGVuZHBvaW50OiAnL2NvbnRhY3RzJyxcbiAgICAgIGRhdGE6IHZhbHVlXG4gICAgfSk7XG4gICAgcmV0dXJuIHtcbiAgICAgIGV4dGVybmFsX2lkOiBTdHJpbmcocmVzcG9uc2UuZGF0YS5leHRlcm5hbF9pZClcbiAgICB9O1xuICB9XG59O1xuZXhwb3J0IGRlZmF1bHQgYWN0aW9uOyJdLAogICJtYXBwaW5ncyI6ICI7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUNBLFFBQW1CO0FBQ25CLElBQU0sUUFBVSxTQUFPO0FBQUEsRUFDckIsV0FBYSxTQUFPLEVBQUUsU0FBUyxVQUFVO0FBQUEsRUFDekMsYUFBZSxTQUFPO0FBQUEsRUFDdEIsT0FBUyxTQUFPLEVBQUUsTUFBTSxFQUFFLFNBQVMsVUFBVTtBQUMvQyxDQUFDO0FBQ00sSUFBTSxTQUFTO0FBQUEsRUFDcEIsTUFBTTtBQUFBLEVBQ04sYUFBYTtBQUFBLEVBQ2IsU0FBUztBQUFBLEVBQ1QsVUFBVTtBQUFBLElBQ1IsUUFBUTtBQUFBLElBQ1IsTUFBTTtBQUFBLElBQ04sT0FBTztBQUFBLEVBQ1Q7QUFBQSxFQUNBO0FBQUEsRUFDQSxRQUFVLFNBQU87QUFBQSxJQUNmLGFBQWUsU0FBTztBQUFBLEVBQ3hCLENBQUM7QUFBQSxFQUNELE1BQU0sT0FBTyxPQUFPLFVBQVU7QUFDNUIsVUFBTSxXQUFXLE1BQU0sTUFBTSxNQUFNO0FBQUEsTUFDakMsUUFBUTtBQUFBLE1BQ1IsVUFBVTtBQUFBLE1BQ1YsTUFBTTtBQUFBLElBQ1IsQ0FBQztBQUNELFdBQU87QUFBQSxNQUNMLGFBQWEsT0FBTyxTQUFTLEtBQUssV0FBVztBQUFBLElBQy9DO0FBQUEsRUFDRjtBQUNGO0FBQ0EsSUFBTyxpQ0FBUTsiLAogICJuYW1lcyI6IFtdCn0K
