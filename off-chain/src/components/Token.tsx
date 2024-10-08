import React from 'react';

import { 
    Box,
    Card,
    CardBody,
    Heading,
    Stack,
    StackDivider,
    Text,
} from '@chakra-ui/react'

interface TokenProps {
    id?: string;
    name?: string;
    description?: string;
    decimals?: number;
    emissionAmount?: number;
    type?: string;
    boxId?: string;
}

function Token({ id, name, description, decimals, emissionAmount, type, boxId }: TokenProps) {
    
    return (
        <>  
        <Box textAlign={'left'} fontSize={'small'}>
            <Card>

                <CardBody>
                    <Stack divider={<StackDivider />} spacing='4'>
                    <Box>
                        <Heading size='xs' textTransform='uppercase'>
                        ID
                        </Heading>
                        <Text pt='2' fontSize='sm'>
                            {id}
                        </Text>
                    </Box>
                    <Box>
                        <Heading size='xs' textTransform='uppercase'>
                        Name
                        </Heading>
                        <Text pt='2' fontSize='sm'>
                            {name}
                        </Text>
                    </Box>
                    <Box>
                        <Heading size='xs' textTransform='uppercase'>
                        Description
                        </Heading>
                        <Text pt='2' fontSize='sm'>
                            {description}
                        </Text>
                    </Box>
                    <Box>
                        <Heading size='xs' textTransform='uppercase'>
                        decimals
                        </Heading>
                        <Text pt='2' fontSize='sm'>
                            {decimals}
                        </Text>
                    </Box>
                    <Box>
                        <Heading size='xs' textTransform='uppercase'>
                        emission
                        </Heading>
                        <Text pt='2' fontSize='sm'>
                            {emissionAmount}
                        </Text>
                    </Box>
                    <Box>
                        <Heading size='xs' textTransform='uppercase'>
                        type
                        </Heading>
                        <Text pt='2' fontSize='sm'>
                            {type}
                        </Text>
                    </Box>
                    <Box>
                        <Heading size='xs' textTransform='uppercase'>
                        boxId
                        </Heading>
                        <Text pt='2' fontSize='sm'>
                            {boxId}
                        </Text>
                    </Box>
                    
                    </Stack>
                </CardBody>
            </Card>
        </Box>
        </>
    );
};

export default Token;