#ifndef MOVING_AVERAGE_H
#define MOVING_AVERAGE_H


#include "stdint.h"

#define WindowLength 10

typedef struct{
	uint32_t History[WindowLength]; /*Array to store values of filter window*/
	uint32_t Sum;	/* Sum of filter window's elements*/
	uint32_t WindowPointer; /* Pointer to the first element of window*/
}FilterTypeDef;


void Moving_Average_Init(FilterTypeDef* filter_struct);
uint16_t Moving_Average_Compute(uint16_t raw_data, FilterTypeDef* filter_struct);

#endif
