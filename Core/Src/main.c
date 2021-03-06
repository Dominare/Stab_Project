/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2022 STMicroelectronics.
  * All rights reserved.</center></h2>
  *
  * This software component is licensed by ST under Ultimate Liberty license
  * SLA0044, the "License"; You may not use this file except in compliance with
  * the License. You may obtain a copy of the License at:
  *                             www.st.com/SLA0044
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "ringbuffer.h"
#include "fix16.h"
#include "fix16pid.h"
#include "moving_average.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
#define VIN 5000
// #define VREFINT_CAL_ADDR                0x1FFFF7BA  /* datasheet p. 19 */
// #define VREFINT_CAL ((uint16_t*) VREFINT_CAL_ADDR)
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
uint16_t adc[3];
typedef enum{
  NOP,
  INIT=1,
  GET_ADC_1 = 2,
  GET_ADC_2 = 3,
  GET_PWM_C = 4 ,
  GET_CURRENT = 5,
  SET_CURRENT = 6,
  
  SET_PID_POINT = 7,
  GET_PID_POINT = 8,
  GET_PID_ERROR = 9,
  GET_PID_OUTPUT = 10,
  SET_PID_KP = 11,
  SET_PID_KD = 12,
  SET_PID_KI = 13,
  SET_PID_ENABLED = 14

} commands;

typedef struct
{
  uint8_t cmd;
  int16_t arg;
} __attribute__((packed, aligned(1))) cmd_t;

uint8_t flag = 0;
uint8_t adc_flag = 0;
volatile uint8_t uart_rx_byte;

ring_buffer_t uart_ring_buffer;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */

  LL_APB1_GRP2_EnableClock(LL_APB1_GRP2_PERIPH_SYSCFG);
  LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_PWR);

  /* System interrupt init*/
  /* SysTick_IRQn interrupt configuration */
  NVIC_SetPriority(SysTick_IRQn, 3);

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_DMA_Init();
  MX_GPIO_Init();
  MX_ADC_Init();
  MX_TIM3_Init();
  MX_USART1_UART_Init();
  MX_TIM14_Init();
  /* USER CODE BEGIN 2 */
  // HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
  LL_TIM_CC_EnableChannel(TIM3, LL_TIM_CHANNEL_CH1);
   LL_TIM_EnableCounter(TIM3);
   LL_TIM_EnableIT_UPDATE(TIM14);
   LL_TIM_EnableCounter(TIM14);
  LL_USART_EnableIT_RXNE(USART1);
  LL_DMA_ConfigAddresses(DMA1,
                         LL_DMA_CHANNEL_1,
                         LL_ADC_DMA_GetRegAddr(ADC1, LL_ADC_DMA_REG_REGULAR_DATA),
                         (uint32_t)&adc,
                         LL_DMA_DIRECTION_PERIPH_TO_MEMORY);
  /* Set DMA transfer size */
  LL_DMA_SetDataLength(DMA1,
                         LL_DMA_CHANNEL_1,
                       3);
  /* Enable DMA transfer interruption: transfer complete */
  LL_DMA_EnableIT_TC(DMA1,
                        LL_DMA_CHANNEL_1);
  /* Enable DMA transfer interruption: half transfer */
  LL_DMA_EnableIT_HT(DMA1,
                        LL_DMA_CHANNEL_1);
  /* Enable DMA transfer interruption: transfer error */
  LL_DMA_EnableIT_TE(DMA1,
                        LL_DMA_CHANNEL_1);
  /*## Activation of DMA #####################################################*/
  /* Enable the DMA transfer */
  LL_DMA_EnableChannel(DMA1,
                       LL_DMA_CHANNEL_1);

  LL_ADC_Enable(ADC1);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  cmd_t rx,tx;

  volatile int16_t current = 0;
  uint16_t filtred[2];
  uint16_t output = 0;
  uint16_t V_ref = 0;
  uint16_t loop_back = 0;
  fix16_t control = 0;
  fix16_t temp = 0;
  uint8_t pid_enable_flag = 0;
  PIDController pid = { PID_KP, PID_KI, PID_KD,
                          PID_TAU,
                          PID_LIM_MIN, PID_LIM_MAX,
	                      PID_LIM_MIN_INT, PID_LIM_MAX_INT,
                          SAMPLE_TIME_S };

    PIDController_Init(&pid);
  FilterTypeDef filterStruct0;
  FilterTypeDef filterStruct1;

  Moving_Average_Init(&filterStruct0);
  Moving_Average_Init(&filterStruct1);
  LL_mDelay(100);
  
  // LL_GPIO_ResetOutputPin(GPIOF, LL_GPIO_PIN_0);
// loop_back = 700;
// pid_enable_flag = 1;

  while (1)
  {
    if(ring_buffer_num_items(&uart_ring_buffer)>=3){
      ring_buffer_dequeue_arr(&uart_ring_buffer,(char *)&rx,3);
      switch (rx.cmd)
      {
      case INIT:
        tx.cmd = INIT;
        tx.arg = 111;
        break;
      case GET_ADC_1:
        tx.cmd = GET_ADC_1;
        tx.arg = filtred[0];
        break;
      case GET_ADC_2:
        tx.cmd = GET_ADC_2;
        tx.arg = filtred[1];
        break;
      case GET_PWM_C:
        tx.cmd = GET_PWM_C;
        tx.arg =(int16_t)fix16_to_int(control);
        break;
      case GET_CURRENT:
        tx.cmd = GET_CURRENT;
        tx.arg = current;
        break;
      case SET_CURRENT:
        tx.cmd = SET_CURRENT;
        tx.arg = current;
        output = (VIN*1-(10*(rx.arg+4)))/2;
        if(rx.arg>1){
        LL_GPIO_ResetOutputPin(GPIOF, LL_GPIO_PIN_0);
        LL_TIM_OC_SetCompareCH1(TIM3,output);
        } else {
          LL_GPIO_SetOutputPin(GPIOF, LL_GPIO_PIN_0);
        }
        break;
      case SET_PID_POINT:
        tx.cmd = SET_PID_POINT;
        loop_back = rx.arg;
        tx.arg = loop_back;
        break;
      case GET_PID_POINT:
        tx.cmd = GET_PID_POINT;
        tx.arg = loop_back;
        break;
      case SET_PID_KD:
        tx.cmd = SET_PID_KD;
        tx.arg = fix16_to_int(pid.Kd);
        temp = fix16_from_int(rx.arg);
        pid.Kd = fix16_div(temp,fix16_from_int(100));
        break;
      case SET_PID_KI:
        tx.cmd = SET_PID_KI;
        tx.arg = fix16_to_int(pid.Ki);
        temp = fix16_from_int(rx.arg);
        pid.Ki = fix16_div(temp,fix16_from_int(100));
        break;
      case SET_PID_KP:
        tx.cmd = SET_PID_KP;
        tx.arg = fix16_to_int(pid.Kp);
        temp = fix16_from_int(rx.arg);
        pid.Kp = fix16_div(temp,fix16_from_int(100));
        break;
      case GET_PID_OUTPUT:
        tx.cmd = GET_PID_OUTPUT;
        tx.arg = fix16_to_int(control);
        break;
      case GET_PID_ERROR:
        tx.cmd = GET_PID_ERROR;
        tx.arg = fix16_to_int(pid.error);
        break;
      case SET_PID_ENABLED:
        tx.cmd = SET_PID_ENABLED;
        tx.arg = pid_enable_flag;
        pid_enable_flag = rx.arg;
        if(pid_enable_flag){
        LL_GPIO_ResetOutputPin(GPIOF, LL_GPIO_PIN_0);
        } else {
          LL_GPIO_SetOutputPin(GPIOF, LL_GPIO_PIN_0);
        }
        break;      
      
      default:
        break;
      }
      USART_TX((uint8_t*)&tx,3);
    };

    if(adc_flag){
      // LL_GPIO_TogglePin(GPIOF, LL_GPIO_PIN_0);
      adc_flag=0;
      //rolling average
      uint16_t VREF_DATA = *VREFINT_CAL_ADDR;
      V_ref = VREFINT_CAL_VREF*VREF_DATA/adc[2];
      adc[0] = 3300*adc[0]/4095;
      adc[1] =  3300*adc[1]/4095;
      filtred[0] = Moving_Average_Compute(adc[0], &filterStruct0);//(3*filtred[0]+adc[0])>>2;
      filtred[1] = Moving_Average_Compute(adc[1], &filterStruct1);//adc[1];(3*filtred[1]+adc[1])>>2;
      if(pid_enable_flag){
      control =  PIDController_Update(&pid, fix16_from_int(loop_back), fix16_from_int(filtred[1]),SAMPLE_TIME_S);
      LL_TIM_OC_SetCompareCH1(TIM3,3299-fix16_to_int((control)));
      }
      current = (VIN-2*filtred[0])/1-40;

       

    }

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  LL_FLASH_SetLatency(LL_FLASH_LATENCY_1);
  while(LL_FLASH_GetLatency() != LL_FLASH_LATENCY_1)
  {
  }
  LL_RCC_HSI_Enable();

   /* Wait till HSI is ready */
  while(LL_RCC_HSI_IsReady() != 1)
  {

  }
  LL_RCC_HSI_SetCalibTrimming(16);
  LL_RCC_HSI14_Enable();

   /* Wait till HSI14 is ready */
  while(LL_RCC_HSI14_IsReady() != 1)
  {

  }
  LL_RCC_HSI14_SetCalibTrimming(16);
  LL_RCC_PLL_ConfigDomain_SYS(LL_RCC_PLLSOURCE_HSI_DIV_2, LL_RCC_PLL_MUL_8);
  LL_RCC_PLL_Enable();

   /* Wait till PLL is ready */
  while(LL_RCC_PLL_IsReady() != 1)
  {

  }
  LL_RCC_SetAHBPrescaler(LL_RCC_SYSCLK_DIV_1);
  LL_RCC_SetAPB1Prescaler(LL_RCC_APB1_DIV_1);
  LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_PLL);

   /* Wait till System clock is ready */
  while(LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_PLL)
  {

  }
  LL_Init1msTick(32000000);
  LL_SetSystemCoreClock(32000000);
  LL_RCC_HSI14_EnableADCControl();
  LL_RCC_SetUSARTClockSource(LL_RCC_USART1_CLKSOURCE_PCLK1);
}

/* USER CODE BEGIN 4 */
void USART1_RX_Callback(){
  ring_buffer_queue(&uart_ring_buffer, LL_USART_ReceiveData8(USART1));
  // HAL_UART_Receive_IT(&huart1,&uart_rx_byte,1);
  
}

void ADC_Callback(){
  adc_flag=1;
}

void TIM14_Callback(){
  LL_ADC_REG_StartConversion(ADC1);
  // LL_GPIO_TogglePin(GPIOB, LL_GPIO_PIN_1);
}


/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
