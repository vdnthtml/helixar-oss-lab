import { createAction } from 'nango';
import * as z from 'zod';

const input = z.object({
    tenant_id: z.string().endsWith('.invalid'),
    external_id: z.string(),
    email: z.string().email().endsWith('.invalid')
});

export default createAction({
    description: 'Compile-only synthetic contact connector; never executed by O06',
    version: '1.0.0',
    endpoint: { method: 'POST', path: '/o06/contacts', group: 'O06 Synthetic' },
    input,
    output: z.object({ external_id: z.string() }),
    exec: async (nango, value) => {
        const response = await nango.proxy({
            method: 'POST',
            endpoint: '/contacts',
            data: value
        });
        return { external_id: String(response.data.external_id) };
    }
});
