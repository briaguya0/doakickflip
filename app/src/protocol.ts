import { type CustomScheme, net } from 'electron';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const appScheme: CustomScheme = {
  scheme: 'app',
  privileges: {
    standard: true,
    secure: true,
    supportFetchAPI: true,
  },
};

const rendererDir = path.join(__dirname, `../renderer/${FRONTEND_VITE_NAME}`);

const isInRendererDir = (file: string) => {
  const relativePath = path.relative(rendererDir, file);
  return (
    !!relativePath &&
    !relativePath.startsWith('..') &&
    !path.isAbsolute(relativePath)
  );
};

// https://www.electronjs.org/docs/latest/api/protocol#protocolhandlescheme-handler
export const handleAppProtocol = (req: Request) => {
  const { host, pathname } = new URL(req.url);
  if (host !== FRONTEND_VITE_NAME) {
    return new Response('not found', { status: 404 });
  }

  const pathToServe = path.join(rendererDir, pathname);

  if (!isInRendererDir(pathToServe)) {
    return new Response('bad', { status: 400 });
  }

  return net.fetch(pathToFileURL(pathToServe).toString());
};
