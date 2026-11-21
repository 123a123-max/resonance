import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
const proxy={'/api':'http://127.0.0.1:8000','/uploads':'http://127.0.0.1:8000'};
const allowedHosts=['.trycloudflare.com'];
export default defineConfig({plugins:[react()],server:{host:true,allowedHosts,proxy},preview:{host:true,port:3002,strictPort:true,allowedHosts,proxy}});
