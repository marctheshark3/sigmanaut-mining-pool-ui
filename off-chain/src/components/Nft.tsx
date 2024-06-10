import React from 'react';

import { 
    Box,
    Card,
    CardBody,
    Heading,
    Image,
    Stack,
    Text,
} from '@chakra-ui/react'

interface NftProps {
    name?: string;
    description?: string;
    r9?: string;
}

function Nft({ name, description, r9 }: NftProps) {
    
    return (
        <>  
            <Box textAlign={'left'} fontSize={'small'}>
                <Card maxW='sm'>
                    <CardBody>
                        <Image src={r9} />
                        <Stack mt='6' spacing='3'>
                        <Heading size='md'>
                            {name}
                            </Heading>
                        <Text>
                            {description}
                        </Text>
                        </Stack>
                    </CardBody>
                </Card>
            </Box>
        </>
    );
};

export default Nft;