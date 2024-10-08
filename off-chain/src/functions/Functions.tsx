export function truncateString(str: string, len: number, sep: string) {
    if (str.length < len) {
        return str;
    } else {
        return (
        str.substring(0, (len / 2)) +
        sep +
        str.substring(str.length - (len / 2), str.length)
        );
    } 
}


export function resolveIpfs(url: string) {
    const ipfsPrefix = 'ipfs://'
    if (!url.startsWith(ipfsPrefix)) return url
    else return url.replace(ipfsPrefix, 'https://cloudflare-ipfs.com/ipfs/')
}


export function toUtf8String(hex: string) {
    if(!hex){
        hex = ''
    }
    var str = '';
    for (var i = 0; i < hex.length; i += 2) {
        str += String.fromCharCode(parseInt(hex.substr(i, 2), 16));
    }
    return str;
}